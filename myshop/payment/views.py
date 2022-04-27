import braintree
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from orders.models import Order
from .tasks import payment_completed
from shop import metrics

# instantiate Braintree payment gateway
gateway = braintree.BraintreeGateway(settings.BRAINTREE_CONF)


@metrics.REQUEST_TIME.time()
@metrics.EXCEPTIONS.count_exceptions(ValueError)
@metrics.PROGRESS.track_inprogress()
def payment_process(request):
    metrics.REQUESTS.labels(view_function='payment_process').inc()
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id)
    total_cost = order.get_total_cost()

    if request.method == 'POST':
        # retrieve nonce
        nonce = request.POST.get('payment_method_nonce', None)
        # create and submit transaction
        result = gateway.transaction.sale(
            {'amount': f'{total_cost:.2f}',
             'payment_method_nonce': nonce,
             'options': {'submit_for_settlement': True}
             }
        )
        if result.is_success:
            # mark the order as paid
            order.paid = True
            # store the unique transaction id
            order.braintree_id = result.transaction.id
            order.save()
            # launch asynchronous task
            payment_completed.delay(order.id)
            return redirect('payment:done')
        else:
            return redirect('payment:cancelled')
    else:
        # generate token
        client_token = gateway.client_token.generate()
        return render(request, 'payment/process.html', {'order': order, 'client_token': client_token})


@metrics.REQUEST_TIME.time()
@metrics.EXCEPTIONS.count_exceptions(ValueError)
@metrics.PROGRESS.track_inprogress()
def payment_done(request):
    metrics.REQUESTS.labels(view_function='payment_done').inc()
    return render(request, 'payment/done.html')


@metrics.REQUEST_TIME.time()
@metrics.EXCEPTIONS.count_exceptions(ValueError)
@metrics.PROGRESS.track_inprogress()
def payment_cancelled(request):
    metrics.REQUESTS.labels(view_function='payment_done').inc()
    return render(request, 'payment/cancelled.html')

