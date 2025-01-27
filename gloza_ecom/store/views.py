from django.shortcuts import render,redirect
from django.views.generic import View
from store.forms import SignUpForm,SignInForm,OrderForm
from django.core.mail import send_mail
from store.models import User,Product,Size,BasketItem,OrderItem
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from decouple import config
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator


RZP_KEY_ID=config('RZP_KEY_ID')
RZP_KEY_SECRET=config('RZP_KEY_SECRET')


# Create your views here.
def send_otp_phone(otp):
    from twilio.rest import Client
    account_sid =config('ACCOUNT_SID') 
    auth_token = config('AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    message = client.messages.create(
    from_='+17166663856',
    body=otp,
    to='+919074417477'
    )
    print(message.sid)


def send_otp_email(user):
    user.generate__otp()
    send_otp_phone(user.otp)
    subject="verify your mail"
    message=f"otp for account verification is {user.otp}"
    from_email="rifafathima2324@gmail.com"
    to_email=[user.email]
    send_mail(subject,message,from_email,to_email)





decorators=[login_required, never_cache]

class SignUpView(View):
    template_name="signup.html"
    form_class=SignUpForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class()
        return render(request,self.template_name,{"form":form_instance})


    def post(self,request,*args,**kwargs):
        form_data=request.POST  
        form_instance=self.form_class(form_data)
        if form_instance.is_valid():
            user_object=form_instance.save(commit=False)
            user_object.is_active=False
            user_object.save()
            send_otp_email(user_object)
            return redirect("verify-email")
        return render(request,self.template_name,{"form":form_instance})


class VerifyEmailView(View):
    template_name="verifyemail.html" 
    def get(self,request,*args,**kwargs):
        return render(request,self.template_name) 

    def post(self,request,*args,**kwargs):
        otp=request.POST.get("otp")
        try:

            user_object=User.objects.get(otp=otp)
            user_object.is_active=True
            user_object.is_verified=True
            user_object.otp=None
            user_object.save()
            return redirect("signin")

        except: 
            messages.error("invalid otp")
            return render(request,self.template_name) 


class SignInView(View):
    template_name="Signin.html"
    form_class=SignInForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class()
        return render(request,self.template_name,{"form":form_instance})
    def post(self,request,*args,**kwargs):
        form_data=request.POST
        form_instance=self.form_class(form_data)
        if form_instance.is_valid():
            uname=form_instance.cleaned_data.get("username")
            pwd=form_instance.cleaned_data.get("password")
            user_object=authenticate(request,username=uname,password=pwd)

            if user_object:
                login(request,user_object)
                return redirect("list")
        return render(request,self.template_name,{"form":form_instance}) 

# @method_decorator(decorators,name='dispatch')
# class SignOutView(View):
#     def get(self,request,*args,**kwargs):
#         logout(request)
#         return redirect("signin")


@method_decorator(never_cache,name='dispatch')
class ProductListView(View):
    template_name="index.html"
    def get(self,request,*args,**kwargs):
        qs=Product.objects.all()
        return render(request,self.template_name,{"data":qs})  

@method_decorator(never_cache,name='dispatch')
class ProductDetailView(View):
    template_name="detail.html"
    def get(self,request,*args,**kwargs):
        id=kwargs.get ("pk")
        qs=Product.objects.get(id=id)   
        return render(request,self.template_name,{"data":qs}) 

@method_decorator(decorators,name='dispatch')
class AddToCartView(View):
    template_name="detail.html"
    def post(self,request,*args,**kwargs):

        id=kwargs.get("pk")
        product_obj=Product.objects.get(id=id)

        try:

            size=request.POST.get("size")
            quantity=request.POST.get("quantity")
            size_object=Size.objects.get(name=size)
            basket_object=request.user.cart

            BasketItem.objects.create(
                Product_object=product_obj,
                size_object=size_object,
                quantity=quantity,
                basket_object=basket_object
            )

            print("item added to cart")
            return redirect("cart-summary")


        except:
            print("error")
            return render(request,self.template_name,{"data":product_obj})

@method_decorator(decorators,name='dispatch')
class CartSummaryView(View):
    template_name="cart_summary.html"
    def get(self,request,*args,**kwars):
        qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)
        basket_total=sum([bi.item_total for bi in qs])
        
        return render(request, self.template_name,{"basket_items":qs,"basket_total":basket_total})


@method_decorator(decorators,name='dispatch')
class CartItemDeleteView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        BasketItem.objects.get(id=id).delete()
        return redirect("cart-summary")  

@method_decorator(decorators,name='dispatch')
class PlaceOrderView(View):
    template_name="place_order.html"
    form_class=OrderForm

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()
        qs=request.user.cart.cart_item.filter(is_order_placed=False)
        total_order_price=sum([bi.item_total for bi in qs])

        
        return render(request,self.template_name,{"form":form_instance,"items":qs,"total_price":total_order_price})

    def post(self,request,*args,**kwargs):
        form_data=request.POST
        form_instance=self.form_class(form_data)

        if form_instance.is_valid():
            form_instance.instance.customer=request.user
            order_instance=form_instance.save()

            basket_items=request.user.cart.cart_item.filter(is_order_placed=False)
            payment=form_instance.cleaned_data.get('payment')
            print(payment)

            for bi in basket_items:
                OrderItem.objects.create(
                    order_object=order_instance,
                    Product_object=bi.Product_object,
                    quantity=bi.quantity,
                    size_object=bi.size_object,
                    price=bi.Product_object.price

                )
                bi.is_order_placed=True
                bi.save()

            if payment == 'ONLINE':
                client=razorpay.Client(auth=(RZP_KEY_ID,RZP_KEY_SECRET))
                amount=sum([bi.item_total for bi in basket_items])*100
                data={"amount":amount,"currency":"INR","receipt":"order_rcptid_11"}

                try:
                    payment=client.order.create(data=data)

                except:
                    return redirect("order-summary")

                rzp_order_id=payment.get('id')


                order_instance.rzp_order_id=rzp_order_id
                order_instance.save()


                name=request.user.username
                email=request.user.email
                phone=request.user.phone


                context={
                    'amount':amount,
                    'key_id':RZP_KEY_ID,
                    'order_id':rzp_order_id,
                    'currency':'INR',
                    'name':name,
                    'email':email,
                    'phone':phone,
                }

                return render(request,'payment.html', context)

            return redirect("order-summary")



                
@method_decorator(decorators,name='dispatch')
class OrderSummaryView(View):

    template_name = 'order_summary.html'

    def get(self, request, *args, **kwargs):

        
        qs = reversed(request.user.orders.all())

        return render(request, self.template_name, {'orders':qs})


@method_decorator([never_cache,csrf_exempt],name='dispatch')
class PaymentVerificationView(View):
    def post(self,request,*args,**kwargs):
        client=razorpay.Client(auth=(RZP_KEY_ID,RZP_KEY_SECRET))
        try:
            client.utility.verify_payment_signature(request.POST)
            print("payment success")

            order_id=request.POST.get('razorpay_order_id')
            order_object=Order.objects.get(rzp_order_id=order_id) 
            order_object.is_paid=True
            order_object.save()


        except:
            print('payment failed')

        print(request.POST) 
        return redirect("order-summary")

        






            






        





            



     


