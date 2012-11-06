from .models import *
from django.contrib.auth.models import User, Group
from django import forms
from smartmin.views import *
from smartmin.users.views import *
from django.core.mail import send_mail
import random
import string
import datetime 


class UserForgetForm(forms.Form):
     email = forms.CharField(label="Your Email",)

class UserRecoverForm(UserForm):
     new_password = forms.CharField(label="New Password", widget=forms.PasswordInput, required=True)
     confirm_new_password = forms.CharField(label="Confirm new Password", widget=forms.PasswordInput, required=True)
     
     def clean_confirm_new_password(self):
        if(not self.cleaned_data['confirm_new_password'] and self.cleaned_data['new_password']):
            raise forms.ValidationError("Confirm the new password by filling the this field")

        if(self.cleaned_data['new_password'] != self.cleaned_data['confirm_new_password']):
            raise forms.ValidationError("New password doesn't match with its confirmation")
        return self.cleaned_data['new_password']

class UserCRUDL(UserCRUDL):
     actions = ('create','update','list', 'register', 'forget','profile', 'recover')

     class Register(SmartCreateView):
        form_class = UserForm
        permission = None
        success_message = "User Registered Successfully."
        success_url = '@users.user_login'
        fields = ('username', 'new_password', 'first_name', 'last_name', 'email', )
        field_config = {
            'groups': dict(help="Users will only get those permissions that are allowed for their group."),
            'new_password': dict(label="Password"),
            'groups': dict(help="Users will only get those permissions that are allowed for their group."),
            'new_password': dict(help="Set the user's initial password here."),
        }

        
            
        def post_save(self, obj):
            """
            Make sure our groups are up to date
            """
            group = Group.objects.get(name="Viewers")
            obj.groups.add(group)

            return obj

     class Forget(SmartFormView):
          form_class = UserForgetForm
          permission = None
          success_message = "User Registered Successfully."
          success_url = "users.user_login"
          fields = ('email', )

          def get_success_url(self):
               return reverse(self.success_url)

          def form_valid(self, form):
               email = form.cleaned_data['email']
               if email:
                    try:
                         user = User.objects.get(email=email)

                         if user:
                              RecoveryToken.objects.filter(email=email).delete()
                              token = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
                              RecoveryToken.objects.create(token=token,email=email)
                              

                              user.email_user("Password Recover mail", "this message is containing the link to recover your password \n http://%s/users/user/recover/%s/" % (self.request.META['SERVER_NAME'],token),"website@klab.rw")
                    except:

                         send_mail('Password Recover', "you have asked to recover your password but you do not have an account on our website", 'website@klab.rw', [email], fail_silently=False)
              
               messages.success(self.request, self.derive_success_message())
               return super(UserCRUDL.Forget, self).form_valid(form)

     class Recover(SmartUpdateView):
          form_class = UserRecoverForm
          permission = None
          success_message = "User Password Updated Successfully. Now you can login using the new password."
          success_url = '@users.user_login'
          fields = ('new_password', 'confirm_new_password')

          field_config = {
               'new_password': dict(help="You can reset your password by entering a new password here."),
               'confirm_new_password': dict(help="Confirm your new password by entering exactly the new password here."),
               }

          def derive_title(self):
               return "Reset your Password"

          def get_object(self, queryset=None):
               token = self.kwargs.get('token')
               token_obj= RecoveryToken.objects.get(token=token)
               return User.objects.get(email=token_obj.email)
