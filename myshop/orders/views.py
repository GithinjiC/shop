import weasyprint
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import OrderItem, Order
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created
from shop import metrics


@metrics.REQUEST_TIME.time()
@metrics.EXCEPTIONS.count_exceptions(ValueError)
@metrics.PROGRESS.track_inprogress()
def order_create(request):
    metrics.REQUESTS.labels(view_function='order_create').inc()
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])
            # clear the cart
            cart.clear()
            # launch asynchronous task
            order_created.delay(order.id)
            # set the order in the session
            request.session['order_id'] = order.id
            return redirect(reverse('payment:process'))
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})


@metrics.REQUEST_TIME.time()
@metrics.EXCEPTIONS.count_exceptions(ValueError)
@metrics.PROGRESS.track_inprogress()
@staff_member_required
def admin_order_detail(request, order_id):
    metrics.REQUESTS.labels(view_function='admin_order_detail').inc()
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order/detail.html', {'order': order})


@metrics.REQUEST_TIME.time()
@metrics.EXCEPTIONS.count_exceptions(ValueError)
@metrics.PROGRESS.track_inprogress()
@staff_member_required
def admin_order_pdf(request, order_id):
    metrics.REQUESTS.labels(view_function='admin_order_pdf').inc()
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order_id}.pdf'
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')])
    return response
