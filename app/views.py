from django.shortcuts import render,redirect,get_object_or_404

# from project.project.settings import EMAIL_HOST_USER
from .models import Post, Like, Comment
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
import random
from django.core.mail import send_mail
from .models import EmailOTP
from django.conf import settings
from django.core.mail import send_mail



def post_list(request):
    posts = Post.objects.all().order_by('-created_at')

    for post in posts:
        post.like_count = post.likes.filter(value=True).count()
        post.dislike_count = post.likes.filter(value=False).count()

        post.user_reaction = None
        if request.user.is_authenticated:
            like = post.likes.filter(user=request.user).first()
            if like:
                post.user_reaction = like.value  # True or False

    return render(request, 'app/post_list.html', {'posts': posts})

def sign_in(request):
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        from django.contrib.auth import authenticate, login
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('post_list')
        else:
            messages.error(request, 'Invalid username or password. Please try againNNNN')
    return render(request, 'app/sign_in.html')    

    
def sign_up(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'app/sign_up.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('sign_up')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('sign_up')

        # CREATE USER AS INACTIVE
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.is_active = False
        user.save()

        # CREATE OTP
        otp = str(random.randint(100000, 999999))
        EmailOTP.objects.create(user=user, otp=otp)

        send_mail(
            'Email Verification OTP',
            f'Your OTP is {otp}',
            settings.EMAIL_HOST_USER,
            [email],
        )

        request.session['otp_user_id'] = user.id

        messages.success(request, 'Check your email for OTP.')
        return redirect('verify_otp')

    return render(request, 'app/sign_up.html')



def create_post(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        # logged-in user
        user = request.user

        # create post
        Post.objects.create(
            user=user,
            title=title,
            content=content,
            image=image
        )

        return redirect('post_list')  # or redirect to detail page

    return render(request, 'app/create_post.html')

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('sign_in')


# @login_required
# def delete_comment(request, comment_id):
#     # CHANGED: Added new view to delete comments
#     # Only the comment owner or post owner can delete
#     comment = get_object_or_404(Comment, id=comment_id)
#     post_slug = comment.post.slug
    
#     Check if the user is the comment owner or the post owner
#     if request.user == comment.user or request.user == comment.post.user:
#         comment.delete()
    
#     return redirect('post_detail', post_slug=post_slug)


def post_detail(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("sign_in")

        text = request.POST.get("comment_text")

        if text and text.strip():
            Comment.objects.create(
                post=post,
                user=request.user,
                comment_text=text
            )

        return redirect("post_detail", post_slug=post_slug)

    comments = post.comments.all().order_by("-created_at")

    return render(request, "app/post_detail.html", {
        "post": post,
        "comments": comments
    })

def home(request):
    users = User.objects.all()
    return render(request, 'app/home.html', {'users': users})

def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=profile_user).order_by('-created_at')

    # Check if current user is following this profile
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    # Get accurate counts
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
    }
    return render(request, 'app/profile.html', context)


@login_required
def like_post(request, slug, action): # • action → "like" or "dislike"
    # CHANGED: Added JsonResponse import to return JSON instead of redirect
    from django.http import JsonResponse
    post = get_object_or_404(Post, slug=slug) # browser request (who clicked, which user) 

    like_obj, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )
    
# Django checks:

# “Is there already a Like row for this user + this post?”
#-------------------------------------------------------------------------------
# Case 1: Already exists
# Django gets it
# created = False
#-------------------------------------------------------------------------------
# Case 2: Does NOT exist
# Django creates it
# created = True
# Because of this line in your model:
# unique_together = ('user', 'post')
# One user → one post → only one Like row.

    if action == "like":
        like_obj.value = True
    else:
        like_obj.value = False
    like_obj.save()
    
#  If user clicked Like → value = True
#  If user clicked Dislike → value = False

# 📌 Same database row is reused
# 📌 Only value changes

    # CHANGED: Instead of redirect("post_list"), now count likes/dislikes and return JSON
    # This allows JavaScript to update the page without refreshing
    like_count = post.likes.filter(value=True).count()   # count of likes using related name ==> related_name = 'likes'
    dislike_count = post.likes.filter(value=False).count()# count of dislikes using related name ==> related_name = 'likes'
    
    return JsonResponse({
        'likes': like_count,
        'dislikes': dislike_count
    })
    
    
    
def search_user(request):
    query = request.GET.get('q')
    users = []

    if query:
        users = User.objects.filter(username__icontains=query)

    return render(request, 'app/search.html', {
        'users': users,
        'query': query
    })
    
    
@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)

    if request.user != user_to_follow:
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )

        if not created:
            follow.delete()  # unfollow

    return redirect('user_profile', username=username)


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=profile_user)

    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()

    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user
        ).exists()

    return render(request, 'app/profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following
    })


@login_required
def following_feed(request):

    # users that I follow
    following_users = Follow.objects.filter(
        follower=request.user
    ).values_list('following', flat=True)

    # posts by followed users + my posts
    posts = Post.objects.filter(
        user__in=following_users
    ).order_by('-created_at')

    return render(request, 'app/following_feed.html', {
        'posts': posts
    })

@login_required
def followers_list(request, username):
    user = get_object_or_404(User, username=username)

    followers = Follow.objects.filter(
        following=user
    ).select_related('follower')

    return render(request, 'app/followers_list.html', {
        'profile_user': user,
        'followers': followers
    })

@login_required
def following_list(request, username):
    user = get_object_or_404(User, username=username)

    following = Follow.objects.filter(
        follower=user
    ).select_related('following')

    return render(request, 'app/following_list.html', {
        'profile_user': user,
        'following': following
    })


@login_required
def post_likes(request, slug):
    post = get_object_or_404(Post, slug=slug)

    likes = Like.objects.filter(
        post=post,
        value=True
    ).select_related('user')

    return render(request, 'app/post_likes.html', {
        'post': post,
        'likes': likes
    })

from django.http import JsonResponse
from django.contrib.auth.models import User

def ajax_search_users(request):
    query = request.GET.get('q', '')
    users = []

    if query:
        qs = User.objects.filter(username__icontains=query)[:5]  # top 5 suggestions
        users = [user.username for user in qs]

    return JsonResponse({'users': users})


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        logout(request)      # logout first
        user.delete()        # then delete
        return redirect('post_list')

    return render(request, 'app/delete_account.html')


@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    # allow only owner
    if post.user != request.user:
        return HttpResponseForbidden("You cannot delete this post")

    if request.method == "POST":
        post.delete()
        return redirect('post_list')  # or profile page

    return redirect('post_detail', post_slug=slug)


@login_required
def my_profile(request):
    user = request.user

    profile = Profile.objects.get(user=user)
    posts = Post.objects.filter(user=user).order_by('-created_at')

    posts_count = posts.count()
    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()

    context = {
        'profile': profile,
        'posts': posts,
        'posts_count': posts_count,
        'followers_count': followers_count,
        'following_count': following_count,
    }
    return render(request, 'app/my_profile.html', context)


@login_required
def delete_post1(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if post.user != request.user:
        return HttpResponseForbidden("Not allowed")

    if request.method == "POST":
        post.delete()
        return redirect('user_profile', request.user.username)




def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        email_otp = EmailOTP.objects.filter(otp=otp).last()

        if email_otp:
            user = email_otp.user
            user.is_active = True
            user.save()
            email_otp.delete()
            messages.success(request, 'Email verified successfully')
            return redirect('sign_in')
        else:
            messages.error(request, 'Invalid OTP')

    return render(request, 'app/verify_otp.html')

# app/views.py
import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import PasswordResetOTP
from django.contrib import messages
from project.settings import EMAIL_HOST_USER

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email not found")
            return redirect('forgot_password')

        otp = str(random.randint(100000, 999999))
        PasswordResetOTP.objects.create(user=user, otp=otp)

        send_mail(
            'Password Reset OTP',
            f'Your OTP is {otp}. It will expire in 5 minutes.',
            EMAIL_HOST_USER,
            [email],
        )

        request.session['reset_user'] = user.id  # store user in session for verification
        # changed by Copilot: previously redirected to 'verify_otp' (email OTP); now using 'verify_otp1' for password reset OTP flow
        return redirect('verify_otp1')

    return render(request, 'app/forgot_password.html')


def verify_otp1(request):
    user_id = request.session.get('reset_user')
    if not user_id:
        return redirect('forgot_password')

    if request.method == "POST":
        otp_input = request.POST.get('otp')
        user = User.objects.get(id=user_id)
        otp_obj = PasswordResetOTP.objects.filter(user=user).last()

        if otp_obj and otp_obj.otp == otp_input and not otp_obj.is_expired():
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid or expired OTP")
            # changed by Copilot: keep user on 'verify_otp1' so PasswordResetOTP is checked (was 'verify_otp' before)
            return redirect('verify_otp1')

    return render(request, 'app/verify_otp1.html')


from django.contrib.auth.hashers import make_password

def reset_password(request):
    user_id = request.session.get('reset_user')
    if not user_id:
        return redirect('forgot_password')

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        if password == confirm:
            user.password = make_password(password)
            user.save()
            messages.success(request, "Password reset successful")
            return redirect('sign_in')
        else:
            messages.error(request, "Passwords do not match")
    
    return render(request, 'app/reset_password.html')

