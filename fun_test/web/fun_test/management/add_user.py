from web.fun_test.django_interactive import *
from django.contrib.auth.models import User as AuthUser


users_info = [("paritosh.joshi@fungible.com", "Paritosh", "Joshi"),
              ("arpit.arora@fungible.com", "Arpit", "Arora"),
              ("ashwini.nanjappa@fungible.com", "Ashwini", "Nanjappa"),
              ("manjunath.madakasira@fungible.com", "Manjunath", "Madakasira"),
              ("nimesh.chaudhary@fungible.com", "Nimesh", "Chaudhary"),
              ("shashank.kadakiya@fungible.com", "Shashank", "Kadakiya"),
              ("devendra.chaudhary@fungible.com", "Devendra", "Chaudhary"),
              ("kapil.suri@fungible.com", "Kapil", "Suri"),
              ("karthik.siddavaram@fungible.com", "Karthik", "Siddavaram")]


for user_info in users_info:

    username = user_info[0]
    first_name = user_info[1]
    last_name = user_info[2]
    if not AuthUser.objects.filter(username=username).exists():
        auth_user = AuthUser(username=username, first_name=first_name, last_name=last_name, email=username)
        auth_user.save()
        auth_user.set_password('fun123fun123')
        auth_user.save()