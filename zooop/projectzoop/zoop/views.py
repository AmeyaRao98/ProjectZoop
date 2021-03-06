from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth import login, authenticate
from .forms import *
from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Following, UserDetails, PostReaction
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import viewsets
from .serializers import PostSerializer, UserDetailsSerializer
from PIL import Image
from rest_framework.exceptions import APIException
from io import BytesIO
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import sys
from emoji.unicode_codes import UNICODE_EMOJI
import random
from django.contrib.auth.decorators import login_required

# Create your views here.
def index(request, page_number = 1):

    if request.method == 'POST':
        form = AddPostForm(request.POST)
        if form.is_valid():
            new_form = form.save(commit = False)
            new_form.user_id = request.user.id
            new_form.original_poster_id = request.user.id
            new_form.save()
            return redirect('index')
    current_user = request.user
    post_list = Post.objects.filter()[:500]
    if request.user.is_authenticated:
        followed_users = Following.objects.filter(user = request.user).values('followed_user')
        post_list = Post.objects.filter(Q(user__id__in = followed_users) |
                                    Q(user__id = request.user.id))
    paginator = Paginator(post_list, 10)
    d = 4
    if page_number + d > paginator.num_pages:
        overflow = page_number + d - paginator.num_pages
        fi = page_number - overflow - d
        if fi < 1:
            fi = 1
        pagination_range = range(fi, paginator.num_pages + 1)
    elif page_number - d < 1:
        overflow = d - page_number + 1
        fi = page_number + d + overflow + 1
        if fi > paginator.num_pages + 1:
            fi = paginator.num_pages + 1
        pagination_range = range(1, fi)
    else :
        pagination_range = range(page_number - d, page_number + d + 1)
    posts = paginator.get_page(page_number)
    add_post_form = AddPostForm()
    return render(request, 'zoop/timeline_page.html',
                            {'add_post_form' : None,
                            'posts' : posts,
                            'emoji' : get_random_emoji()[:1],
                            'pagination_range': pagination_range,
                            'visitor' : False,
                            'reacts' : get_reaction_list(),
                            'react_count' : get_reactions_count_dict(posts.object_list),
                            'current_reacts': get_reactions_dict(request.user.id, posts.object_list),
                            'user_object' : current_user})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data = request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'zoop/login.html', {'form': form})

@login_required
def account(request):
    response = request.GET.get('file', None)
    return render(request, 'zoop/account.html', {'file_response' : response})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')

            user = authenticate(username=username, password=raw_password)
            UserDetails(pk=user.id).save()
            login(request, user)
            return redirect('index')
    else:
        form = UserRegistrationForm()
    return render(request, 'zoop/register.html', {'form': form})

def profile(request, userid = -1, page_number = 1):
    return redirect('userprofile', userid = userid, page_number = page_number, permanent=True)

def userprofile(request, userid = -1, page_number = 1):

    if userid == -1:
        userid = request.user.id

    visitor = True
    followed = True
    if request.user.id == userid:
        visitor = False
    else:
        try:
            Following.objects.get(user_id = request.user.id,
                                followed_user_id = userid)
        except ObjectDoesNotExist:
            followed = False


    add_post_form = AddPostForm()

    if request.method == 'POST':
        form = AddPostForm(request.POST)
        if form.is_valid():
            new_form = form.save(commit = False)
            new_form.user_id = request.user.id
            new_form.original_poster_id = request.user.id
            new_form.save()
            return redirect('/profile/'+ str(request.user.id) + '/1')
        else:
            add_post_form = form
    #print(settings.AUTH_USER_MODEL.models)
    #user = User.objects.get(id = userid)
    user = get_object_or_404(User, id = userid)


    post_list = Post.objects.filter(user_id = userid)
    paginator = Paginator(post_list, 10)
    d = 4
    if page_number + d > paginator.num_pages:
        overflow = page_number + d - paginator.num_pages
        fi = page_number - overflow - d
        if fi < 1:
            fi = 1
        pagination_range = range(fi, paginator.num_pages + 1)
    elif page_number - d < 1:
        overflow = d - page_number + 1
        fi = page_number + d + overflow + 1
        if fi > paginator.num_pages + 1:
            fi = paginator.num_pages + 1
        pagination_range = range(1, fi)
    else :
        pagination_range = range(page_number - d, page_number + d + 1)
    posts = paginator.get_page(page_number)
    return render(request, 'zoop/timeline_page.html',
                            {'posts' : posts,
                            'add_post_form' : add_post_form,
                            'visitor': visitor,
                            'emoji' : get_random_emoji()[:1],
                            'pagination_range': pagination_range,
                            'followed': followed,
                            'reacts' : get_reaction_list(),
                            'react_count' : get_reactions_count_dict(posts.object_list),
                            'current_reacts': get_reactions_dict(request.user.id, posts.object_list),
                            'user_object': user})

def testing(request):
    if request.method == 'POST':
        form = AddPostForm(request.POST)
        if form.is_valid():
            new_form = form.save(commit = False)
            new_form.user_id = request.user.id
            new_form.original_poster_id = request.user.id
            new_form.save()
    add_post_form = AddPostForm()
    posts = Post.objects.filter(user_id = request.user.id)[:10]
    return render(request, 'zoop/testing.html',
                            {'add_post_form' : add_post_form,
                            'posts' : posts,})

def follow(request, userid):
    Following.objects.get_or_create(user_id = request.user.id,
                            followed_user_id = userid)
    return redirect('/profile/' + str(userid))

def unfollow(request, userid):
    Following.objects.get(user_id = request.user.id,
                            followed_user_id = userid).delete()
    return redirect('/profile/' + str(userid))

def rezoop(request, post_id):
    og_post = Post.objects.get(pk = post_id)
    if og_post.user_id != request.user.id:
        Post.objects.get_or_create(user_id = request.user.id,
                            content = og_post.content,
                            original_poster_id = og_post.user_id)
    next = request.POST.get('next', '/')
    return HttpResponseRedirect(next)

def react(request, post_id, react_id):
    if request.method == 'POST':
        post = Post.objects.get(pk = post_id)
        try:
            reaction = PostReaction.objects.get(user_id = request.user.id,
                                                post_id = post_id,
                                                react_type = react_id)
            reaction.delete()
        except:
            PostReaction(user_id = request.user.id,
                        post_id = post_id,
                        react_type = react_id).save()

        next = request.POST.get('next', '/')
        return HttpResponseRedirect(next)




def unreact(request, post_id):
    pass

def delete_post(request, post_id):
    post = Post.objects.get(pk = post_id)
    if request.user.id == post.user.id:
        Post.objects.get(pk=post_id).delete()
    next = request.POST.get('next', '/')
    return HttpResponseRedirect(next)

def search(request):
    srch = request.GET.get('phrase','')
    if srch == '':
        results = User.objects.none()
        details = User.objects.none()
    else:
        results = User .objects.filter(username__icontains = srch)[:25]
        details = UserDetails.objects.filter(user__id__in = results)[:25]
    return render(request, 'zoop/search.html', {'results' : results,
                                                'details' : details})


class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows a user's posts list to be retrieved.
    Parameters:
    "user" - Insert the user-name of the user you want to retrieve posts of.
    "count" - Insert number of recent posts to be retrieved. (min 1, max 30)

    """
    def get_queryset(self):
        user_id = self.request.query_params.get('user', None)
        number = int(self.request.query_params.get('count', 1))
        number = max(1, min(number, 50));
        queryset = Post.objects.filter(user_id = user_id)[:number]
        if not queryset:
            raise APIException("The provided username does not exist in the database")
        return queryset

    serializer_class = PostSerializer

def upload_avatar(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            m = UserDetails.objects.get(pk=request.user.id)
            try:
                image = Image.open(form.cleaned_data['image'])
                out_img = BytesIO()
                #filename=str(form.cleaned_data['image'])
                filename = str(request.user.id) + '.jpg'
                image = image.resize((200,200))
                image.save(out_img, format='JPEG', quality=100)
                out_img.seek(0)
            except:
                return redirect('/account?file=bad')
            m.avatar.delete()
            m.avatar = InMemoryUploadedFile(out_img,'ImageField', filename, 'image/jpeg', sys.getsizeof(out_img), None)

            #m.avatar = form.cleaned_data['image']
            m.save()
            return redirect('/account?file=ok')
        else:
            return redirect('/account?file=bad')
    return HttpResponseForbidden('allowed only via POST')


def get_reaction_list():
    return ['💯', '😂', '😠', '😞', '😲', '🤔']

def get_reactions_dict(user_id, posts_queryset):
    ids = posts_queryset.values_list('post_id', flat=True)
    react_dict = {}
    for i in ids:
        try:
            reaction = PostReaction.objects.get(user_id = user_id, post_id = i)
            react_dict[i] = int(reaction.react_type)
        except:
            react_dict[i] = None

    for i in ids:
            post_reactions = PostReaction.objects.filter(post_id = i)
            react_dict['count_'+str(i)] = post_reactions.count()

    return react_dict

def get_reactions_count_dict(posts_queryset):
    ids = posts_queryset.values_list('post_id', flat=True)
    react_count = {}
    for i in ids:
        for y in range(1,7):
            reactions = PostReaction.objects.filter(post_id = i, react_type = y).count()
            react_count[(i,y)] = reactions
    return react_count


def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('account')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ChangePasswordForm(request.user)
    return render(request, 'registration/change_password.html', {
        'form': form
    })

def get_random_emoji():
    return(random.choice(list(UNICODE_EMOJI.keys())))
