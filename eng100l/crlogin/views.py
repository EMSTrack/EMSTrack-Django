from django.shortcuts import render, redirect 
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required # Maria added
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout, login
from django.contrib import auth  # needed for logout 

# Create your views here.


# TODO: if user is logged in, redirect to home page 
# TODO: probably dont even need this 
# OR move implementation from User app
class LoginPageView(TemplateView):
    #print("Wrong one")
    def get(self, request, **kwargs):
        return render(request, 'login.html', context=None)

    def post(self, request, **kwargs):
        print ("wrong one")
        return render(request, 'login.html', context=None)


def user_login(request):
    
    if request.method == "GET":  
        print("YASS")
        if request.user.is_authenticated():
            return HttpResponseRedirect("/ambulances") 
            print("User is logged in ")
        else: 
            return render(request, 'login.html')

  
    if request.method == "POST":
        print ("This is POST login")
        email = request.POST.get('email')
        password = request.POST.get('password')
        print("email: ", email)
        print("password: ", password)
        user = authenticate(username=email, password=password)
        if user:
            #User is successfully authenticated
            login(request,user)
            print("Logged in user name: ", user.first_name)
            success = "Welcome! You have successfully logged in. "
            return HttpResponseRedirect("/ambulances")
            #return render(request, 'home.html', {})
            # return HttpResponseRedirect('/')
        else:
            error = "Email and Password did not match. Please try again."
            return render(request, 'login.html',{'error':error})


def user_signup(request):
    
    if request.method == "GET":  
        print("YASS")
        if request.user.is_authenticated():
            return HttpResponseRedirect("/ambulances") 
            print("User is logged in ")
        else: 
            return render(request, 'signup.html')


    if request.method == 'POST':
        # TODO: need to save name, phone number etc
        name = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        pass_1 = request.POST.get('password1')
        pass_2 = request.POST.get('password2')
        first_name = name.split(" ",1)[0]
        last_name = name.split(" ",1)[1]
        print ("email: ", email)
        if pass_1 == pass_2:
            if user_exists(email):
                print ("USER EXISTS!!!")
                # user already exists
                error = "User with this email already exists."
                return render(request, 'signup.html', {'error':error})

            else:  
                print ("USER DOES NOT EXIST")
                user = User.objects.create_user(
                                              username=email,
                                              email=email,
                                              password=pass_1,
                                              first_name=first_name, 
                                              last_name=last_name
                                             )
                return HttpResponseRedirect("/auth/login/")
        else:
             error = "Passwords Do Not Match"
             return render(request, 'signup.html',{"error":error})
    else:
        return render(request, 'signup.html')


def user_logout(request):
    #if request.method == "GET": 
    try: 
        #del request.session['phone']  # Not sure if this is needed
        auth.logout(request)
        return HttpResponseRedirect("/auth/login/")
    except: 
        return HttpResponse("Error occurred when logging out")

class AboutPageView(TemplateView):
    template_name = "about.html"


class HomePageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'home.html', {})

    def post(self, request, **kwargs):
        username = None
        if request.user.is_authenticated():
            username = request.user.username
            return render(request, 'home.html', {})

# added this for user in session 
def redirect_view(request):
    if not request.user.is_authenticated(): 
        return redirect('/login/?next=%s' % request.path)


def user_exists(username):
    if User.objects.filter(username=username).exists():
        return True

    return False

# Settings 
def user_settings(request):

    if request.method == 'POST':

        if request.user.is_authenticated():
            phone = request.user.username
            pass_c = request.POST.get('currpassword')
            pass_1 = request.POST.get('password1')
            pass_2 = request.POST.get('password2')
            user_check = authenticate(username=phone, password=pass_c)

            if user_check:
                if pass_1 == pass_2:
                    user = User.objects.get(username=phone)
                    user.set_password(pass_1)
                    user.save()
                    success = "Successfully changed password."
                    login(request, user)
                    return HttpResponseRedirect("/ambulances")
            
                else:
                    error = " Password Mismatch "
                    return render(request, 'settings.html',{"error":error})
            
            else:
                error = "Phone Number and Password didn't match, Please try again."
                return render(request, 'settings.html',{"error":error})
        
        else:
            return render(request, '/login/')
    
    else:
        return render(request, 'settings.html')
