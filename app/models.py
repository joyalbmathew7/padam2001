from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from PIL import Image, ExifTags

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to="post_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        # -------- Slug Creation --------
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug

        super().save(*args, **kwargs)

        # -------- Image Compression + Fix Rotation --------
        if self.image:
            img = Image.open(self.image.path)

            # Fix rotation using EXIF
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                    
                exif = img._getexif()
                if exif is not None:
                    orientation_value = exif.get(orientation)

                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
                        # Value Meaning Easy explanation
                        # 1	Normal	No rotation needed
                        # 3	Rotate 180°	Photo is upside down
                        # 6	Rotate 90° right	Turn clockwise
                        # 8	Rotate 90° left	Turn anticlockwise
            except:
                pass  # ignore EXIF issues

            # Resize + compress
            max_size = (800, 800)
            img.thumbnail(max_size)
            img.save(self.image.path, quality=70)

    def __str__(self):
        return self.title

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)
    value = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'post')



class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


    #  ADD THIS
    # parent = models.ForeignKey(
    #     'self',
    #     related_name='replies',
    #     null=True,
    #     blank=True,
    #     on_delete=models.CASCADE
    # )


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User,
        related_name='followers_list',
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower} follows {self.following}"

    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_images/', default='default.jpg')

    def __str__(self):
        return self.user.username


    
    
# class Post(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     content = models.TextField()

#     def __str__(self):
#         return self.user.username


