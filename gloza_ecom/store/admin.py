from django.contrib import admin

from store.models import Tag,Size,Category,Product

from store.models import User

# Register your models here.
admin.site.register(User)
admin.site.register(Tag)
admin.site.register(Size)
admin.site.register(Category)
admin.site.register(Product)
