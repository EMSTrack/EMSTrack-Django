from django.shortcuts import render, redirect 
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required # Maria added
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group, Permission  # needed for user groups and permissions
from django.contrib.auth import authenticate, logout, login
from django.contrib import auth  # needed for logout 
from django.contrib.contenttypes.models import ContentType # needed for permissions 
#from django.core.mail import EmailMultiAlternatives  # for email confirmation registration 

 
# Create your views here.


# TODO: if user is logged in, redirect to home page 
# TODO: probably dont even need this 
# OR move implementation from User app
class LoginPageView(TemplateView):

	def get(self, request, **kwargs):
		return render(request, 'login.html', context=None)

	def post(self, request, **kwargs):
		print ("wrong one")
		return render(request, 'login.html', context=None)


# User login logic. 
def user_login(request):
    print ("Request: ")
    print(request)

    if request.method == "POST":
        print ("This is POST request for login")
        # get email and login for authenrication 
        email = request.POST.get('email')
        password = request.POST.get('password')

        print("email: ", email)
        print("password: ", password)

        # authenticate a user
        user = authenticate(username=email, password=password)
        # log user in after successful authentication. 
        if user is not None and user.is_active:
            #User is successfully authenticated
            login(request, user)
            print("Logged in user name: ", user.first_name, " ", user.last_name)
            return HttpResponseRedirect("/ambulances")
        # user was not authenticated, display error message    
        else:
            error = "Email and Password did not match. Please try again."
            return render(request, 'login.html',{'error':error})
    else:
        print("GET login method")
        if request.user.is_authenticated(): 
        	return HttpResponseRedirect("/auth/login")
        else: 
        	return render(request, 'login.html')



# User signup 
def user_signup(request):
    if request.method == 'POST': 

        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        email = request.POST.get('email')
        pass_1 = request.POST.get('password1')
        pass_2 = request.POST.get('password2')
        user_group = request.POST.get('position')
        
        print("request: ")
        print(request)
        print(request.POST)

        # if entered passwords match 
        if pass_1 == pass_2:
            # user already exists
            if user_exists(email):
              print ("USER EXISTS!!!")
              error = "User with this email already exists."
              return render(request, 'signup.html', {'error':error})

            # user does not exist 
            else:  
              print ("USER DOES NOT EXIST")

              # create user with given information 
              user = User.objects.create_user(
                                              username=email,
                                              email=email,
                                              password=pass_1,
                                              first_name=first_name, 
                                              last_name=last_name
                                             )

              # create appropriate user group for the user
              group = Group.objects.get(name=user_group)
              group.user_set.add(user)


              #send_mail("Activation", "Click here to activate your account", settings.DEFAULT_FROM_EMAIL, email)
              #mail = EmailMultiAlternatives('Activation', 'Click here to activate', 'donotreply@nodomain.com', [email])
              #mail.send()

              # create_user does not save to db. Can modify user object before calling save() 
              # add user group
              #user.groups.add(group)
              #user.save()
              return HttpResponseRedirect("/auth/login/")

        else:
             error = "Passwords Do Not Match"
             return render(request, 'signup.html',{"error":error})
    else:
         return render(request, 'signup.html')


def user_logout(request): 
  try: 
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

