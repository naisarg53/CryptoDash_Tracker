import stripe
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt

from .forms import UserRegisterForm
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from pycoingecko import CoinGeckoAPI
import requests
import json
from django.conf import settings
from django.http.response import JsonResponse, HttpResponse
from .models import PurchaseHistory,CoinsDetails



#################### index #######################################
def index(request):

    response = CoinGeckoAPI()

    get_price_change = requests.get(f'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=7').json()
    get_trending_data = requests.get(f'https://api.coingecko.com/api/v3/search/trending').json()
    get_global_trends = requests.get(f'https://api.coingecko.com/api/v3/global').json()
    get_top_market_category = requests.get(f'https://api.coingecko.com/api/v3/coins/categories').json()

    return render(request, 'user/index.html', {'title':'index', 'response': response.get_coins, 'trends': get_trending_data, 'get_price_change': get_price_change, 'get_global_data': get_global_trends, 'get_top_category': get_top_market_category})

def detail(request, coin_name):
    response = CoinGeckoAPI()

    get_price_change = requests.get(f'https://api.coingecko.com/api/v3/coins/{coin_name}/market_chart?vs_currency=usd&days=7').json()
    request.session['coin_name'] = coin_name

    return render(request, 'user/detail.html', {'title': 'detail', 'response': response.get_coins, 'get_line_chart': get_price_change, 'get_coin_name': coin_name})

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
def create_checkout_session(request):

    coin_name = request.session['coin_name']
    get_coin_details = requests.get(f'https://api.coingecko.com/api/v3/coins/{coin_name}').json()

    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                line_items=[
                    {
                        'images': [get_coin_details['image']['large']],
                        'name': get_coin_details['name'],
                        'quantity': 1,
                        'currency': 'usd',
                        'amount': int(round(float(get_coin_details['market_data']['current_price']['usd']),2)*100),
                    }
                ],
                metadata={'coin_id':get_coin_details['id']},
            )
            request.session['session_id'] = checkout_session.id
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

#http://localhost:8000/success/?session_id=cs_test_a1avHehgAd95AELxtgEgXHQJSHqQ9WmMPP3qroozxta4spUIFEExmaHixn
# http://localhost:8000/success/?session_id=cs_test_a1NqAmW024NmJ44GFu5tB5tzaHJxcWA08Y2GiXPUhx11aDS3M7WC3sFl5o
def SuccessView(request):
    session = request.GET.get('session_id', '')
    stripe.api_key = settings.STRIPE_SECRET_KEY
    line_items = stripe.checkout.Session.list_line_items(session)
    subTotal = line_items.data[0]['amount_subtotal']/100
    coinType =line_items.data[0]["description"]
    qty=line_items.data[0]["quantity"]
    coin_id=stripe.checkout.Session.retrieve(session)['metadata']['coin_id']
    userName=request.user.username
    # data = {subTotal, qty, coinType, userName}
    b = PurchaseHistory(username=userName, coin_name=coinType, sub_Total=subTotal,quantity=qty,coin_id=coin_id)
    b.save()
    #get_data = PurchaseHistory(request.GET)
    return render(request, 'user/success.html', {'get_payment_details':b, 'get_session': session})

def CancelledView(request):
    return render(request, 'user/cancelled.html')

def orderHistory(request):
    userName = request.user.username
    orderData=PurchaseHistory.objects.filter(username=userName)
    
    return render(request, 'user/orders.html', {'orderData': orderData})

def fetchList():
    getCoinDetails= requests.get(f'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&page=1').json()
    for item in getCoinDetails:
            details=CoinsDetails.objects.create(id=item["id"],symbol=item["symbol"],name=item["name"],image=item["image"])
            details.save()

""" Portfolio view """
def portfoilio(request):
    # fetchList()
    userName = request.user.username
    userOrders = PurchaseHistory.objects.filter(username=userName)
    coins=[]
    data={}

    for i in userOrders:  #get all coins type from user order
        if i.coin_id not in coins:
            coins.append(i.coin_id)
            data[i.coin_id]={}

    for coinType in coins:
        getCurrentPrice=requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={coinType}&vs_currencies=usd').json()
        currentPrice=getCurrentPrice[coinType]['usd']   #get current price of the coin in coins array

        all_coin_order=userOrders.filter(coin_id=coinType) #get all user orders for the coinType
        coinHolding=0
        netCost=0.0
        for coinOrder in all_coin_order:
            coinHolding+=coinOrder.quantity
            netCost+=float(coinOrder.sub_Total)

        data[coinType]['image'] = CoinsDetails.objects.get(id=coinType).image
        data[coinType]['name'] = CoinsDetails.objects.get(id=coinType).name
        data[coinType]['symbol'] = CoinsDetails.objects.get(id=coinType).symbol
        data[coinType]['coinHolding']=coinHolding
        data[coinType]['netCost'] = netCost

        currentMarketValue=float(coinHolding * currentPrice)
        data[coinType]['marketValue'] = round(currentMarketValue,2)

        netProfitOrLoss=float(currentMarketValue-netCost)
        data[coinType]['change'] = round(netProfitOrLoss,2)
        if netCost != 0:
            percenChange = netProfitOrLoss * 100 / netCost
        else:
            percenChange=0
        data[coinType]['percentage_change'] = round(percenChange, 2)

    #Total investment data
    totalData={'total_invest':0,'c_market':0,'t_profit':0,'t_change':0,'t_holdings':0}
    for ct in coins:
        totalData['total_invest']+=data[ct]['netCost']
        totalData['c_market'] += data[ct]['marketValue']
        totalData['t_holdings'] += data[ct]['coinHolding']

    totalData['t_profit']=round(totalData['c_market']-totalData['total_invest'],2)
    if totalData['total_invest'] != 0:
        totalData['t_change'] = round(totalData['t_profit'] * 100/ totalData['total_invest'],2)
    else:
        totalData['t_change']=0
    totalData['c_market']=round(totalData['c_market'],2)
    return render(request, 'user/portfolio.html',{'data':data,'total_data':totalData})

########### register here #####################################
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            ######################### mail system ####################################
            htmly = get_template('user/Email.html')
            d = { 'username': username }
            subject, from_email, to = 'welcome', 'naisarg.pandya8853@gmail.com', email
            html_content = htmly.render(d)
            msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            ##################################################################
            messages.success(request, f'Your account has been created ! You are now able to log in')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form, 'title':'reqister here'})


################ login forms###################################################
def Login(request):
    if request.method == 'POST':

        # AuthenticationForm_can_also_be_used__

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password)
        request.session['user_name'] = username
        if user is not None:
            form = login(request, user)
            messages.success(request, f' welcome {username} !!')
            return redirect('index')
        else:
            messages.info(request, f'account done not exit plz sign in')
    form = AuthenticationForm()
    return render(request, 'user/login.html', {'form':form, 'title':'log in'})

def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "password/password_reset_email.txt"
                    c = {
                        "email":user.email,
                        'domain':'127.0.0.1:8000',
                        'site_name': 'Website',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, 'admin@example.com', [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect("/password_reset/done/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password/password_reset.html", context={"password_reset_form":password_reset_form})

