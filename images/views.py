from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ImageCreateForm
from .models import Image
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from actions.utils import create_action
import redis
from django.conf import settings


@login_required
def image_create(request):
    """
    Представление хранения изображения на сайте
    """
    if request.method == 'POST':
        # форма отправлена
        form = ImageCreateForm(data=request.POST)
        if form.is_valid():
            # данные в форме валидны
            cd = form.cleaned_data
            new_image = form.save(commit=False)
            # назначить текущего пользователя элементу
            new_image.user = request.user
            new_image.save()
            # создать действие, которое отражает добавление изображения
            create_action(request.user, 'bookmarked image', new_image)
            # сообщение об успехе и перенаправление на список изображений
            messages.success(request, 'Изображение было успешно добавлено')
            # перенаправить к представлению детальной информации о только что созданном элементе
            return redirect(new_image.get_absolute_url())
    else:
        # скомпоновать форму с данными, предоставленными букмарклетом  методом GET
        form = ImageCreateForm(data=request.GET)
    return render(request, 'images/image/create.html', {'section': 'images', 'form': form})


def image_detail(request, id, slug):
    """
    Представление детальной информации об изображении
    """
    image = get_object_or_404(Image, id=id, slug=slug)
    # увеличить общее число просмотров изображения на 1
    total_views = r.incr(f'image: {image.id}: views')
    # увеличивать рейтинг изображения на 1
    r.zincrby('image_ranking', 1, image.id)
    return render(request,
                  'images/image/detail.html',
                  {'section': 'images', 'image': image, 'total_views': total_views})


@login_required
@require_POST
def image_like(request):
    """
    Реализация представления действия like и unlike
    """
    image_id = request.POST.get('id')
    action = request.POST.get('action')
    if image_id and action:
        try:
            image = Image.objects.get(id=image_id)
            if action == 'like':
                image.users_like.add(request.user)
                create_action(request.user, 'likes', image)
            else:
                image.users_like.remove(request.user)
            return JsonResponse({'status': 'ok'})
        except Image.DoesNotExist:
            pass
    return JsonResponse({'status': 'error'})


@login_required
def image_list(request):
    """
    Представление списка изображений
    Бесконечная постраничная прокрутка списка изображений с помощью JavaScript and Python
    """
    images = Image.objects.all()
    paginator = Paginator(images, 8)  # 10 изображений на странице
    page = request.GET.get('page')
    images_only = request.GET.get('images_only')
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        # Если страница не является целым числом,
        # то возвращаем первую страницу.
        images = paginator.page(1)
    except EmptyPage:
        if images_only:
            # Если AJAX-запрос и страница вне диапазона,
            # то возвращаем пустую страницу.
            return HttpResponse('')
        # Если страница вне диапазона и не AJAX-запрос,
        # то возвращаем последнюю страницу.
        images = paginator.page(paginator.num_pages)
    if images_only:
        return render(request,
                      'images/image/list_images.html',
                      {'section': 'images', 'images': images})
    return render(request,
                  'images/image/list.html',
                  {'section': 'images', 'images': images})


#   сохранить с redis
r = redis.Redis(host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB)


@login_required
def image_ranking(request):
    """
    Представление рейтинга изображений
    """
    # получить словарь рейтинга изображений
    image_ranking = r.zrange('image_ranking', 0, -1, desc=True)[:10]
    image_ranking_ids = [int(id) for id in image_ranking]
    # получить наиболее просматриваемые изображения
    most_viewed = list(Image.objects.filter(id__in=image_ranking_ids))
    most_viewed.sort(key=lambda x: image_ranking_ids.index(x.id))

    return render(request,
                  'images/image/ranking.html',
                  {'section': 'images', 'most_viewed': most_viewed})
