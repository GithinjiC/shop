from django.shortcuts import render, get_object_or_404
from .models import Category, Product
from cart.forms import CartAddProductForm
from .recommender import Recommender
from . import metrics


@metrics.REQUEST_TIME.time()
@metrics.EXCEPTIONS.count_exceptions(ValueError)
@metrics.PROGRESS.track_inprogress()
def product_list(request, category_slug=None):
    metrics.REQUESTS.labels(view_function='product_list').inc()
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        language = request.LANGUAGE_CODE
        category = get_object_or_404(Category, translations__language_code=language, translations__slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'shop/product/list.html',
                  {'category': category, 'categories': categories, 'products': products})


@metrics.REQUEST_TIME.time()
@metrics.EXCEPTIONS.count_exceptions(ValueError)
@metrics.PROGRESS.track_inprogress()
def product_detail(request, id, slug):
    metrics.REQUESTS.labels(view_function='product_detail').inc()
    language = request.LANGUAGE_CODE
    product = get_object_or_404(Product, id=id, translations__language_code=language, translations__slug=slug,
                                available=True)
    cart_product_form = CartAddProductForm()
    r = Recommender()
    recommended_products = r.suggest_products_for([product], 4)
    return render(request, 'shop/product/detail.html', {'product': product, 'cart_product_form': cart_product_form,
                                                        'recommended_products': recommended_products})
