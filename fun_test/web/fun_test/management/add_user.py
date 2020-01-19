from web.fun_test.django_interactive import *
from django.contrib.auth.models import User as AuthUser

"""
users_info = [("paritosh.joshi@fungible.com", "Paritosh", "Joshi"),
              ("arpit.arora@fungible.com", "Arpit", "Arora"),
              ("ashwini.nanjappa@fungible.com", "Ashwini", "Nanjappa"),
              ("manjunath.madakasira@fungible.com", "Manjunath", "Madakasira"),
              ("nimesh.chaudhary@fungible.com", "Nimesh", "Chaudhary"),
              ("shashank.kadakiya@fungible.com", "Shashank", "Kadakiya"),
              ("devendra.chaudhary@fungible.com", "Devendra", "Chaudhary"),
              ("kapil.suri@fungible.com", "Kapil", "Suri"),
              ("karthik.siddavaram@fungible.com", "Karthik", "Siddavaram")]

"""
users_info = [
    [
        "akshay.deshpande@fungible.com",
        "Akshay",
        "Deshpande"
    ],
    [
        "ame.wongsa@fungible.com",
        "Ame",
        "Wongsa"
    ],
    [
        "amy.wu@fungible.com",
        "Amy",
        "Wu"
    ],
    [
        "bibek.regmi@fungible.com",
        "Bibek",
        "Regmi"
    ],
    [
        "boris.altshul@fungible.com",
        "Boris",
        "Altshul"
    ],
    [
        "chen.wan@fungible.com",
        "Chen",
        "Wan"
    ],
    [
        "chester.knapp@fungible.com",
        "Chester",
        "Knapp"
    ],
    [
        "chris.sherman@fungible.com",
        "Chris",
        "Sherman"
    ],
    [
        "christina.janczak@fungible.com",
        "Christina",
        "Janczak"
    ],
    [
        "denis.martens@fungible.com",
        "Denis",
        "Martens"
    ],
    [
        "dimitrian.tkachenko@fungible.com",
        "Dimitrian",
        "Tkachenko"
    ],
    [
        "eric.wuerschmidt@fungible.com",
        "Eric",
        "Wuerschmidt"
    ],
    [
        "evgen.masiakin@fungible.com",
        "Evgen",
        "Masiakin"
    ],
    [
        "getnat.ejigu@fungible.com",
        "Getnat",
        "Ejigu"
    ],
    [
        "herman.wu@fungible.com",
        "Herman",
        "Wu"
    ],
    [
        "in.hosok@fungible.com",
        "In",
        "HoSok"
    ],
    [
        "ivy.chen@fungible.com",
        "Ivy",
        "Chen"
    ],
    [
        "jaimin.shah@fungible.com",
        "Jaimin",
        "Shah"
    ],
    [
        "jason.vanvalkenburgh@fungible.com",
        "Jason",
        "Van Valkenburgh"
    ],
    [
        "kosha.parekh@fungible.com",
        "Kosha",
        "Parekh"
    ],
    [
        "kostiantyn.kuzin@fungible.com",
        "Kostiantyn",
        "Kuzin"
    ],
    [
        "lakshmi.nannapaneni@fungible.com",
        "Lakshmi",
        "Nannapaneni"
    ],
    [
        "mayank.khanna@fungible.com",
        "Mayank",
        "Khanna"
    ],
    [
        "michael.nachmias@fungible.com",
        "Michael",
        "Nachmias"
    ],
    [
        "paolo.garcia@fungible.com",
        "Paolo",
        "Garcia"
    ],
    [
        "pradeep.tomar@fungible.com",
        "Pradeep",
        "Tomar"
    ],
    [
        "rachel.kotraba@fungible.com",
        "Rachel",
        "Kotraba"
    ],
    [
        "roderick.kidd@fungible.com",
        "Roderick",
        "Kidd"
    ],
    [
        "ryan.norwood@fungible.com",
        "Ryan",
        "Norwood"
    ],
    [
        "saikiran.mankena@fungible.com",
        "Saikiran",
        "Mankena"
    ],
    [
        "serban.jora@fungible.com",
        "Serban",
        "Jora"
    ],
    [
        "shankha.banerjee@fungible.com",
        "Shankha",
        "Banerjee"
    ],
    [
        "shelby.sweeney@fungible.com",
        "Shelby",
        "Sweeney"
    ],
    [
        "tudor.popescu@fungible.com",
        "Tudor",
        "Popescu"
    ],
    [
        "vedavyas.duggirala@fungible.com",
        "Vedavyas",
        "Duggirala"
    ],
    [
        "venkat.jaligama@fungible.com",
        "Venkat",
        "Jaligama"
    ]
]


for user_info in users_info:

    username = user_info[0]
    first_name = user_info[1]
    last_name = user_info[2]
    if not AuthUser.objects.filter(username=username).exists():
        auth_user = AuthUser(username=username, first_name=first_name, last_name=last_name, email=username)
        auth_user.save()
        auth_user.set_password('fun123fun123')
        auth_user.save()


"""
path = "/Users/johnabraham/Documents/Cloudistics_Fungible_Email_List.csv"
import json
f = open(path, "r")
contents = f.read()
f.close()

my_tuples = []
for line in contents.split("\n"):
    if "Frist" in line:
        continue
    line = line.strip()
    print line.split(",")
    first_name, last_name, cloudistics_email, fungible_email, _ = line.split(",")
    my_tuples.append((fungible_email.lower(), first_name, last_name))




print json.dumps(my_tuples, indent=4)

"""