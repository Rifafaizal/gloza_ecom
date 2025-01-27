from django.db import models
from django.contrib.auth.models import AbstractUser,User
from django.db.models.signals import post_save
from random import randint




# Create your models here.

class User(AbstractUser):
    is_verified=models.BooleanField(default=False)
    otp=models.CharField(max_length=5,null=True,blank=True)
    phone=models.CharField(max_length=10,null=True)

    def generate__otp(self):
        self.otp=str(randint(1000,9000))+str(self.id)
        self.save()

class BaseModel(models.Model):
    created_date=models.DateTimeField(auto_now_add=True)
    updated_date=models.DateTimeField(auto_now=True)
    is_active=models.BooleanField(default=True)


class Category(BaseModel):

    name=models.CharField(max_length=200,default="")
    def __str__(self):
        return self.name


class Size(BaseModel):
    name=models.CharField(max_length=200,)
    def __str__(self):
        return self.name


class Tag(BaseModel):
    name=models.CharField(max_length=200)
    def __str__(self):
        return self.name


class Product(BaseModel):
    title=models.CharField(max_length=200)
    description=models.TextField()
    price=models.PositiveIntegerField()
    picture=models.ImageField(upload_to="product_images",null=True,blank=True)
    color=models.CharField(max_length=200)
    category_object=models.ForeignKey(Category,on_delete=models.CASCADE)
    size_object=models.ManyToManyField(Size)
    tag_object=models.ManyToManyField(Tag)
    def __str__(self):
        return self.title



class Basket(BaseModel):
    owner=models.OneToOneField(User,on_delete=models.CASCADE,related_name="cart")   



class BasketItem(BaseModel):
    Product_object=models.ForeignKey(Product,on_delete=models.CASCADE)  
    quantity=models.PositiveIntegerField(default=1)
    size_object=models.ForeignKey(Size,on_delete=models.CASCADE) 
    is_order_placed=models.BooleanField(default=False) 
    basket_object=models.ForeignKey(Basket,on_delete=models.CASCADE,related_name="cart_item") 

    @property
    def item_total(self):
        return self.quantity * self.Product_object.price

def create_basket(sender,instance,created,**kwargs):
    if created:
        Basket.objects.create(owner=instance) 


post_save.connect(create_basket,User) 


class Order(BaseModel):
    customer=models.ForeignKey(User,on_delete=models.CASCADE,related_name="orders")

    address=models.TextField()

    phone=models.CharField(max_length=15)

    PAYMENT_OPTIONS=(
        ("COD","COD"),
        ("ONLINE","ONLINE")
    )

    payment=models.CharField(max_length=200,choices=PAYMENT_OPTIONS,default="COD")

    rzp_order_id=models.CharField(max_length=100,null=True)

    is_paid=models.BooleanField(default=False)

    @property
    def order_total(self):

        total = sum([oi.item_total for oi in self.orderitems.all()])

        return total


class OrderItem(BaseModel):
    order_object=models.ForeignKey(Order,on_delete=models.CASCADE,related_name="orderitems")
    Product_object=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    size_object=models.ForeignKey(Size,on_delete=models.CASCADE)
    price=models.FloatField()

    @property
    def item_total(self):
        return self.quantity*self.price















