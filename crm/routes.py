from flask import render_template,redirect,flash,url_for,request,abort,session, jsonify
from crm import app,bcrypt, mail, login_manager, photos, celery_app, socketio
from crm.models import Role, db,Category,Customer,Product,OrderDetail,Employee, Order,Shipper,Supplier,User,ModelView,RoleView,UserView,Comment,CustomerOrder,Cargo,Newsletter
from crm.forms import LoginForm,RegistrationForm,ProductForm,UpdateAccountForm,RequestResetForm,ResetPasswordForm,CommentForm
from flask_login import login_required, login_user, current_user, login_user,logout_user
from flask_admin import Admin
from azure.storage.blob import BlobServiceClient
import secrets
import os
from PIL import Image
from flask_mail import Message
import simplejson as json 
import datetime
from flask_socketio import emit
import sys
from celery.schedules import crontab
import paypalrestsdk



# connect_str = ""
# container_name = "images"
# blob_service_client = BlobServiceClient.from_connection_string(conn_str = connect_str)

# try:
#     container_client = blob_service_client.get_container_client(container = container_name)
#     container_client.get_container_properties()

# except Exception as e:
#     container_client = blob_service_client.create_container(container_name)


# def get_pics():
#     blob_items = container_client.list_blobs()
#     image_list = []
#     image_names = []
    
#     for blob in blob_items:
#         blob_client = container_client.get_blob_client(blob=blob.name)
#         image_list.append(blob_client.url)
#         image_names.append(blob_client.blob_name)

    
#     return image_list,image_names

# def upload_pics():
#     filenames = ""
#     for file in request.files.getlist("images"):
#         filenames += file.filename + " "

#         try:
#             container_client.upload_blob(file.filename, file)
#             filenames += file.filename + "<br />"


#         except Exception as e:
#             print(e)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_login_required(function):
    def wrapper(*args,**kwargs):
        if current_user.is_authenticated:
            if current_user.RoleID != 2:
                return abort(401)
            
            else:
                return function()
        else:
            return redirect(url_for("login"))
    return wrapper


def salesman_login_required(function):
    def wrapper(*args,**kwargs):
        if current_user.is_authenticated:
            if current_user.RoleID != 1:
                return abort(401)
            
            else:
                return function()
        else:
            return redirect(url_for("login"))
    return wrapper


@socketio.on('connect')
def ws_connect():
    try:
        with open('crm/static/js/live-user/live-user.txt',"r") as f:
            data = f.read()
            _ = int(json.loads(data).get("counter")) + int(1)
            tem = {"counter": _ }

        emit('user', tem, brodcast=True)
            
        
        with open('crm/static/js/live-user/live-user.txt',"w", encoding="utf-8") as fw:
            fw.write(json.dumps(tem))
        
        emit('user', tem , brodcast=True)
    
    
    except Exception as e:
        with open('crm/static/js/live-user/live-user.txt',"w", encoding="utf-8") as fw:
            fw.write(json.dumps({"counter":0}))
        
        emit('user', {"counter":0}, brodcast=True)

@socketio.on('disconnect')
def ws_disconnect():

    with open('crm/static/js/live-user/live-user.txt',"r") as f:
        data = f.read()
        tem = {"counter": int(json.loads(data).get("counter")) - 1}
            
    
    with open('crm/static/js/live-user/live-user.txt',"w", encoding="utf-8") as fw:
        fw.write(json.dumps(tem))
    
    emit('user', tem , brodcast=True)


employee_mails_query = db.session.query(User.email,User.id,User.name).join(Role,User.RoleID == Role.roleID).filter(User.RoleID == 1)
employee_informations = []


for user_info in employee_mails_query:
    employee_informations.append(user_info)

newsletter_email_list = []
current_emails = db.session.query(Newsletter.email)
for emails in current_emails:
    newsletter_email_list.append(emails[0])

@celery_app.task(name='send_newsletter_mail')
def send_newsletter_email():

    for mails in newsletter_email_list:
        msg = Message("A limited list of discounted products has been prepared for you.", 
        sender = "noreply@virashop.com", 
        recipients = [mails])
        msg.html = render_template('email-template-newsletter.html')
        mail.send(msg)
        print("Newsletter Mail Has Been Sended!")


@celery_app.task(name='send_daily_mail')
def send_daily_email():
    
    for user in employee_informations:
        average_shipping_day = db.session.query(db.func.avg((Order.ShippedDate - Order.OrderDate))).join(OrderDetail,Order.OrderID == OrderDetail.OrderID).join(Product,
        Product.ProductID == OrderDetail.ProductID).filter(Product.CreatorID == user[1])
        total_product_per_user = db.session.query(db.func.count(Product.ProductID)).filter(Product.CreatorID == user[1])
        last_order = db.session.query(Order.OrderID).join(OrderDetail,Order.OrderID == OrderDetail.OrderID).join(Product,
        Product.ProductID == OrderDetail.ProductID).filter(Product.CreatorID == user[1]).order_by((Order.OrderID).desc()).first()
        total_income = db.session.query(db.func.sum(OrderDetail.UnitPrice)).join(Order, 
        Order.OrderID == OrderDetail.OrderID).join(Product,Product.ProductID == OrderDetail.ProductID).filter(Product.CreatorID == user[1])
        employee_name = user[2]

        average_ship_day = []
        last_order_id = []
        total_prd_per_user = []
        t_income = []
        

        for i in average_shipping_day:
            average_ship_day.append(round(i[0]/86400000,2))

        for i in last_order:
            last_order_id.append(i)
        
        for i in total_product_per_user:
            total_prd_per_user.append(i[0])

        for total_amount in total_income:
            t_income.append(float(total_amount[0]))
        
        msg = Message("Your daily statistics are prepared for you!", 
        sender = "noreply@virashop.com", 
        recipients = [user[0]])
        msg.html = render_template('email-template-statistic.html',total_income = json.dumps(t_income[0]),total_product = total_prd_per_user[0],
        average_ship_day = average_ship_day[0],last_order_id = last_order_id[0],employee_name = employee_name)
        mail.send(msg)
        print("Test Mail Has Been Sended!")


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour='*/24'),send_daily_email.s(), name='send_daily_mail')
    sender.add_periodic_task(crontab(hour='*/48'),send_newsletter_email.s(), name='send_newsletter_mail')


@app.route("/newsletter-subscribe", methods = ['POST'])
def newsletter_subscribe():
    email = request.form.get("newsletter")
    email_list = []
    if request.method == "POST":
        current_emails = db.session.query(Newsletter.email)

        for emails in current_emails:
            email_list.append(emails[0])
        

        for i in email_list:
            if i == email:
                flash("You are already subscribed to the newsletter. If you are unable to receive an e-mail, please contact us.",'danger')
                return redirect(request.referrer) 
        
        newsletter = Newsletter(email = email)
        db.session.add(newsletter)
        db.session.commit()
        flash("Registration to the newsletter is successful. We will email you soon. Don't forget to check your spam box.",'success')
        return redirect(request.referrer)


@app.route('/',methods = ['POST','GET'])
def index():

    image_file = url_for('static', filename=f'img/categories/cat-{id}')
    categories = Category.query.all()
    products = Product.query.limit(12)
    
   
    return render_template("index.html", categories=categories , products=products,image_file = image_file)


@app.route("/login",methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            return redirect(url_for("index"))
        else:    
            flash("Username or password is wrong!")
    return render_template("login.html", title="Login", form=form)

@app.route("/register", methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, lastname=form.lastname.data, phone = form.phone.data,  
        username=form.username.data,email=form.email.data, password= hashed_password )
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!','success')
        login_user(user)
        return redirect(url_for("index"))
   
    return render_template("register.html", title="Register", form=form)


def MagerDicts(dict1,dict2):
    if isinstance(dict1,list) and isinstance(dict2,list):
        return dict1 + dict2
    elif isinstance(dict1,dict) and isinstance(dict2,dict):
        return dict(list(dict1.items()) + list(dict2.items()))
    return False


@login_required
@app.route('/addcart', methods = ['POST'])
def AddCart():
    try:
        product_id = request.form.get('product_id')
        creator_id = request.form.get('creator_id')
        quantity = request.form.get('quantity')
        product = db.session.query(Product).filter(Product.ProductID == product_id).first()
        
        if request.method == "POST":
            DictItems = {product_id:{'name': product.ProductName, 'price': product.UnitPrice, 'quantity':quantity, 'seller': creator_id, 'image': product.image_1}}
        
            if 'Shoppingcart' in session:
                print(session['Shoppingcart'])
                if product_id in session['Shoppingcart']:
                    for key,item in session['Shoppingcart'].items():
                        if int(key) == int(product_id):
                            session.modified = True 
                            item['quantity'] = int(item['quantity'])
                            item['quantity'] += int(quantity)
                else:
                    session['Shoppingcart'] = MagerDicts(session['Shoppingcart'], DictItems)
                    return redirect(request.referrer)

            else:
                session['Shoppingcart'] = DictItems
                return redirect(request.referrer)


    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)

@login_required
@app.route("/cart")
def getCart():

    categories = Category.query.all()
    subtotal = 0
    before_shipping_grandtotal = 0

    if 'Shoppingcart' in session:
        for key,product in session['Shoppingcart'].items():
            subtotal += float(product['price']) * int(product['quantity'])
            before_shipping_grandtotal = float("%.2f" % subtotal) 
    
    else:
        [session.pop(key) for key in list(session.keys()) if key == 'Shoppingcart']
        return render_template("cart.html",categories=categories)


    return render_template("cart.html",categories=categories, before_shipping_grandtotal = before_shipping_grandtotal)

@login_required
@app.route("/updatecart/<int:code>", methods = ["POST"])
def updatecart(code):
    if 'Shoppingcart' not in session and len(session['Shoppingcart']) <= 0:
        return redirect(url_for("index"))
    
    if request.method == "POST":
        quantity = request.form.get('quantity')

        try:
            session.modified = True
            for key,item in session['Shoppingcart'].items():
                if int(key) == code:
                    item['quantity'] = quantity
                    return redirect(url_for('getCart'))
        
        except Exception as e:
            print(e)
            return redirect(url_for('getCart'))

@login_required
@app.route("/deleteitem/<int:id>")
def deleteitem(id):
    if 'Shoppingcart' not in session and len(session['Shoppingcart']) <= 0:
        return redirect(url_for("index"))
    
    try:
        session.modified = True
        for key,item in session['Shoppingcart'].items():
            if int(key) == id:
                session['Shoppingcart'].pop(key,None)
                if len(session['Shoppingcart']) <= 0:
                    [session.pop(key) for key in list(session.keys()) if key == 'Shoppingcart']
                    return redirect(url_for('getCart'))
                return redirect(url_for('getCart'))
        
    except Exception as e:
        print(e)
        return redirect(url_for('getCart'))

@login_required
@app.route('/clearcart')
def clearcart():
    try:
        session.pop('Shoppingcart',None)
        [session.pop(key) for key in list(session.keys()) if key == 'Shoppingcart']
        return redirect(url_for('getCart'))
    
    except Exception as e:
        print(e)


paypalrestsdk.configure({
  "mode": "sandbox", # sandbox or live
  "client_id": "",
  "client_secret": "" })


@login_required
@app.route("/payment", methods =['POST'])
def payment():

    if 'Shoppingcart' not in session and len(session['Shoppingcart']) <= 0:
        return redirect(url_for("index"))

    items_dict = []

    for key,item in session['Shoppingcart'].items():
        items_dict.append({"name": item['name'], "price" : item['price'], "currency" : "USD", "quantity" : item['quantity'] })
    
    subtotal = 0
    before_shipping_grandtotal = 0

    for key,product in session['Shoppingcart'].items():
        subtotal += float(product['price']) * int(product['quantity'])
        before_shipping_grandtotal = float("%.2f" % subtotal)
    
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": url_for('order_confirmed_page', _external=True),
            "cancel_url": "http://localhost:5000/"},
        "transactions": [{
            "item_list": {
                "items": items_dict},
            "amount": {
                "total": before_shipping_grandtotal,
                "currency": "USD"},
            }]})

    if payment.create():
        print("Payment Success")
    else:
        print(payment.error)
    
    return jsonify({'paymentID' : payment.id})

@login_required
@app.route("/execute", methods =['POST'])
def execute():

    success = False

    payment = paypalrestsdk.Payment.find(request.form['paymentID'])

    if payment.execute({'payer_id' : request.form['payerID']}):
        print('Execute success!')
        success = True
        invoice = secrets.token_hex(5)

        for key,value in session['Deliveryinfo'].items():
            name = value['name']
            lastname = value['last_name']
            address1 = value['address_1']
            address2 = value['address_2']
            phone_number = value['phone_number']
            city = value['city']
            state = value['state']
            zip_code = value['zip_code']

        customer_id = current_user.id

        order = CustomerOrder(name = name , lastname = lastname, invoice = invoice, address1 = address1, 
        address2 = address2, phone_number = phone_number, city = city, state = state , zip = zip_code, customer_id = customer_id, orders = session['Shoppingcart'])
        db.session.add(order)
        db.session.commit()
        order_confirmed_mail()

        for key,product in session['Shoppingcart'].items():
            product_id = key 
            product_quantity = product['quantity']
            new_stock = Product.query.filter(Product.ProductID == product_id).first()
            new_stock.UnitsInStock = Product.UnitsInStock - int(product_quantity)
            db.session.commit()

        [session.pop(key) for key in list(session.keys()) if key == 'Deliveryinfo']
        [session.pop(key) for key in list(session.keys()) if key == 'Shoppingcart']

        return redirect(url_for('order_confirmed_page'))

    else:
        print(payment.error)

    return jsonify({'success': success})

@app.route("/order-confirmed-page")
def order_confirmed_page():

    categories = Category.query.all()

    return render_template("order-confirmed-page.html",categories=categories)

@login_required
@app.route("/delivery", methods = ['POST', 'GET'])
def delivery():

    if 'Deliveryinfo' in session:
        [session.pop(key) for key in list(session.keys()) if key == 'Deliveryinfo']

    if 'Shoppingcart' not in session:
        flash("Your card is empty!", "warning")
        return redirect(request.referrer)

    name = request.form.get('name')
    last_name = request.form.get('lastname')
    address_1 = request.form.get('address1')
    address_2 = request.form.get('address2')
    phone_number = request.form.get('phone_number')
    city = request.form.get('city')
    state = request.form.get('state')
    zip_code = request.form.get('zip')
    user_id = current_user.id

    if request.method == "POST":

        AddressDictItems = {user_id:{'name' : name , 'last_name' : last_name, 'address_1' : address_1, 
        'address_2' : address_2, 'city': city, 'zip_code': zip_code, 'state': state, 'phone_number': phone_number}}


        if 'Deliveryinfo' in session:
            print(session['Deliveryinfo'])
            return redirect('/complate-payment')

        else:
            session['Deliveryinfo'] = AddressDictItems
            print(session['Deliveryinfo'])   
            return redirect('/complate-payment')


    subtotal = 0
    before_shipping_grandtotal = 0

    for key,product in session['Shoppingcart'].items():
        subtotal += float(product['price']) * int(product['quantity'])
        before_shipping_grandtotal = float("%.2f" % subtotal)
       
    categories = Category.query.all()

    return render_template("delivery.html",before_shipping_grandtotal = before_shipping_grandtotal,categories=categories)


@login_required
@app.route("/complate-payment", methods = ['POST', 'GET'])
def complate_payment():

    if 'Shoppingcart' not in session:
        return redirect("/")
    
    if 'Deliveryinfo' not in session:
        return redirect("/delivery")

    for key,info in session['Deliveryinfo'].items():
        if not info['name'] or not info['last_name'] or not info['address_1'] or not info['address_2'] or not info['city'] or not info['zip_code'] or not info['state'] :
            [session.pop(key) for key in list(session.keys()) if key == 'Deliveryinfo']
            flash("Please fill in your address information completely!")
            return redirect('/delivery')

    subtotal = 0
    before_shipping_grandtotal = 0

    for key,product in session['Shoppingcart'].items():
        subtotal += float(product['price']) * int(product['quantity'])
        before_shipping_grandtotal = float("%.2f" % subtotal) 
        print(product)
    
    categories = Category.query.all()

    return render_template("complate_payment.html", before_shipping_grandtotal = before_shipping_grandtotal,categories=categories)


@app.route("/shop/<int:id>")
def shop(id):
    page = request.args.get('page',1,type=int)
    categories = Category.query.all()
    cat_id = Product.query.filter_by(CategoryId = id).first()
    get_cat_products = Product.query.filter_by(CategoryId = id).paginate(page=page,per_page = 9)

    return render_template("shop.html",get_cat_products = get_cat_products,categories=categories,cat_id = cat_id)


def order_confirmed_mail():
    user_id = current_user.id
    customer_name = db.session.query(CustomerOrder.name).filter(CustomerOrder.customer_id == user_id).order_by(CustomerOrder.id.desc()).first()
    order_id = db.session.query(CustomerOrder.id).filter(CustomerOrder.customer_id == user_id).order_by(CustomerOrder.id.desc()).first()
    orders = db.session.query(CustomerOrder.orders).filter(CustomerOrder.customer_id == user_id).order_by(CustomerOrder.id.desc()).first()
    order_date = datetime.datetime.now().strftime("%d %b, %Y")
    customer_address_1 = db.session.query(CustomerOrder.address1).filter(CustomerOrder.customer_id == user_id).order_by(CustomerOrder.id.desc()).first()
    customer_address_city = db.session.query(CustomerOrder.city).filter(CustomerOrder.customer_id == user_id).order_by(CustomerOrder.id.desc()).first()
    
    customer_name_list = []
    customer_address_list = []
    order_id_list = []
    customer_address_city_list = []
    customer_email_list = [current_user.email]
    total_sub = 0

    for name in customer_name:
        customer_name_list.append(name)
    
    for id in order_id:
        order_id_list.append(id)
    
    for address in customer_address_1:
        customer_address_list.append(address)
    
    for city in customer_address_city:
        customer_address_city_list.append(city)
    
    for _key, prd in orders.orders.items():
        total_sub += float(int(prd['quantity']) * float(prd['price']))
        grand_total = float("%.2f" % total_sub)
    
    print(orders.orders.items())
    
    msg = Message("We got your order!", 
    sender = "noreply@virashop.com", 
    recipients = [customer_email_list[0]])
    msg.html = render_template('order_confirmed_mail.html', order_id = order_id_list[0], order_date = order_date, customer_name_list = customer_name_list[0], 
    total_sub = total_sub, orders=orders, customer_address_city_list = customer_address_city_list[0], customer_address_list = customer_address_list[0],grand_total = grand_total)
    mail.send(msg)
    print("Order Confirmed Mail Has Been Sended!")


@login_required
@app.route("/my-orders")
def my_orders():
    user_id = current_user.id
    all_orders = db.session.query(CustomerOrder).filter_by(customer_id = user_id)
    categories = Category.query.all()

    return render_template('my_orders.html', all_orders = all_orders,categories=categories)

@login_required
@app.route("/order-detail/<int:id>")
def order_detail(id):
    if current_user.is_authenticated:
        
        orders = CustomerOrder.query.get_or_404(id)
        subtotal = 0
        grand_total = 0

        for _key,product in orders.orders.items():
            subtotal += float(product['price']) * int(product['quantity'])
            grand_total = float("%.2f" % subtotal) 

    else:
        return redirect(url_for('login'))
    
    categories = Category.query.all()

    return render_template('order_detail.html', grand_total = grand_total, orders=orders,categories=categories)        


@login_required
@app.route('/employee/dashboard/orders')
def employee_orders():
    if current_user.RoleID == 1 or current_user.RoleID == 2:
        image_file = url_for('static', filename='img/profile_pics/' + current_user.image_file)
        all_orders = db.session.query(CustomerOrder).all()
    
    else:
        abort(403)
   

    return render_template('dashboard/employee_orders.html', image_file = image_file, all_orders = all_orders)

@login_required
@app.route('/employee/dashboard/orders-detail/<int:id>', methods = ['POST', 'GET'])
def employee_orders_detail(id):
    if current_user.RoleID == 1 or current_user.RoleID == 2:
        image_file = url_for('static', filename='img/profile_pics/' + current_user.image_file)
        if current_user.is_authenticated:
            
            orders = CustomerOrder.query.get_or_404(id)
            subtotal = 0
            grand_total = 0

            for _key,product in orders.orders.items():
                subtotal += float(product['price']) * int(product['quantity'])
                grand_total = float("%.2f" % subtotal) 

        else:
            return redirect(url_for('login'))
    
    else:
        abort(403)

    return render_template('dashboard/employee_order_detail.html', grand_total = grand_total, orders=orders,image_file = image_file)

@login_required
@app.route("/employee/dashboard/orders-detail/cargo-update/<int:id>", methods=['POST'])
def cargo_update(id):

    if current_user.RoleID == 1 or current_user.RoleID == 2:
        order = CustomerOrder.query.get_or_404(id)

        if request.method == "POST":

            if request.form['submit_button'] == '0':
                order.order_status = 0
                db.session.commit()
                return redirect(request.referrer)

            elif request.form['submit_button'] == '1':
                order.order_status = 1
                db.session.commit()
                return redirect(request.referrer)
            
            elif request.form['submit_button'] == '2':
                order.order_status = 2
                db.session.commit()
                return redirect(request.referrer)

            elif request.form['submit_button'] == '3':
                order.order_status = 3
                db.session.commit()
                return redirect(request.referrer)
    else:
        abort(403)

@app.route("/employee/dashboard/orders-detail/tracking-save/<int:id>", methods=['POST'])
def tracking_save(id):
    if current_user.RoleID == 1 or current_user.RoleID == 2:
        order = CustomerOrder.query.get_or_404(id)
        tracking_number = request.form.get("tracking_number")
        if request.method == "POST":
            order.tracking_number = tracking_number
            db.session.commit()
            flash("Tracking number added succesfully!", "success")
            return redirect(request.referrer)
    else:
        abort(403)
   
@app.route("/detail/<int:ProductID>", methods = ['POST','GET'])
def detail(ProductID):

    with open('crm/static/js/live-user/live-user.txt',"r") as f:
        data = f.read()
        data = {"counter": int(json.loads(data).get("counter"))}

    form = CommentForm()

    with open('crm/static/js/rating/rating.json') as f:
        ratingstore = json.load(f)
    
    if request.method == 'POST':
        if current_user.is_authenticated:

            five_stars = int(ratingstore['five_stars'])
            four_stars = int(ratingstore['four_stars'])
            three_stars = int(ratingstore['three_stars'])
            two_stars = int(ratingstore['two_stars'])
            one_star = int(ratingstore['one_star'])
            count = int(ratingstore['count'])
            rating = float(ratingstore['rating'])
            total = int(ratingstore['total'])

            if 'rating' in request.form:
                content = int(request.form['rating'])
                if content:
                    if content == 5:
                        five_stars +=1
                    
                    elif content == 4:
                        four_stars +=1
                    
                    elif content == 3:
                        three_stars +=1
                    
                    elif content == 2:
                        two_stars +=1
                    
                    elif content == 1:
                        one_star +=1
                    
                    count +=1
                    total += content
                    rating = float('{0:.1f}'.format(total/count))

            ratingstore['five_stars'] = str(five_stars)
            ratingstore['four_stars'] = str(four_stars)
            ratingstore['three_stars'] = str(three_stars)
            ratingstore['two_stars'] = str(two_stars)
            ratingstore['one_star'] = str(one_star)
            ratingstore['count'] = str(count)
            ratingstore['total'] = str(total)
            ratingstore['rating'] = str(rating)

            with open('crm/static/js/rating/rating.json','w') as f:
                json.dump(ratingstore,f,indent = 2)


            if form.validate_on_submit():
                if not form.comment_text:
                    flash("Comment area can not be empty!","error")
            
            comment = Comment(comment_text = form.comment_text.data , author = current_user.id , product_id = ProductID,rating = content)
            db.session.add(comment)
            db.session.commit()
            flash('Comment added succesfully!', "success")

        else:
            flash('You must be logged in to post a comment.')

    suggested_products = Product.query.limit(5)
    product_details = Product.query.get_or_404(ProductID)
    comments = db.session.query(Comment).filter(Comment.product_id == ProductID)
    categories = Category.query.all()
    avg_prd_point = db.session.query(db.func.avg(Comment.rating)).filter(Comment.product_id == ProductID).first()
    avarage_point = []
    for point in avg_prd_point:
        if point is None:
            avarage_point.append(0)
        else:
            avarage_point.append(round(point,1))
    
    return render_template("detail.html",product_details=product_details,suggested_products = 
    suggested_products, title = product_details.ProductName, categories = categories,form = form, comments = comments, data = data,avarage_point = avarage_point[0])


@login_required
@app.route("/employee/dashboard/add/product", methods=['GET','POST'])
def add_product():
    if current_user.RoleID == 1 or current_user.RoleID == 2:
        image_file = url_for('static', filename='img/profile_pics/' + current_user.image_file)
        form = ProductForm()
        product_creator = current_user.id
        if form.validate_on_submit():
            if form.image_1.data and form.image_2.data and form.image_3.data:
                image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
                image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
                image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")
            product = Product(ProductName = form.ProductName.data, CategoryId = form.CategoryId.data , CreatorID = product_creator , QuantityPerUnit = form.QuantityPerUnit.data, UnitPrice = form.UnitPrice.data,
            UnitsInStock = form.UnitInStock.data, Description = form.Description.data, image_1 = image_1, image_2 = image_2, image_3 = image_3)
            db.session.add(product)
            db.session.commit()
            flash('Product Added Succesfully!', "success")
            return redirect(url_for('dashboard_products'))
        return render_template('add_product.html', title="Add Product",form=form,legend="Create Product",image_file = image_file)
    else:
        abort(403)


@login_required
@app.route("/detail/<int:ProductID>/update", methods=['GET','POST'])
def update_product(ProductID):
    user_id = current_user.id
    product = Product.query.get_or_404(ProductID)

    if current_user.RoleID == 1 or current_user.RoleID == 2:
        product = Product.query.get_or_404(ProductID)
        
        if product.CreatorID != user_id:
            abort(403)
        form = ProductForm()
        if form.validate_on_submit():
            if form.image_1.data:
                image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
                product.image_1 = image_1
            if form.image_2.data:
                image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
                product.image_2 = image_2
            if form.image_3.data:
                image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")
                product.image_3 = image_3

            product.ProductName = form.ProductName.data
            product.CategoryID = form.CategoryId.data
            product.QuantityPerUnit = form.QuantityPerUnit.data
            product.UnitPrice = form.UnitPrice.data
            product.UnitsInStock = form.UnitInStock.data
            product.Description = form.Description.data
            

            db.session.commit()
            flash('Product has been updated!','success')
            return redirect(url_for('dashboard_products'))
        
        elif request.method == 'GET':

            form.ProductName.data = product.ProductName
            form.CategoryId.data = product.CategoryId
            form.QuantityPerUnit.data = product.QuantityPerUnit
            form.UnitPrice.data = product.UnitPrice
            form.UnitInStock.data = product.UnitsInStock
            form.Description.data = product.Description
            form.image_1.data = product.image_1
            form.image_2.data = product.image_2
            form.image_3.data = product.image_3

        return render_template('add_product.html', title="Update Product",form=form, legend="Update Product")
    
    else:
        abort(403)

@login_required
@app.route("/detail/<int:ProductID>/delete", methods=['POST'])
def delete_product(ProductID):
    if current_user.RoleID == 1 or current_user.RoleID == 2:
        product = Product.query.get_or_404(ProductID)
        if product.CreatorID != current_user.id:
            abort(403)
        
        db.session.delete(product)
        db.session.commit()
        flash('Product has been deleted!','warning')

        return redirect(url_for('dashboard_products'))

    else:
        abort(403)


def Convert(a):
    it = iter(a)
    res_dct = dict(zip(it, it))
    return res_dct


@login_required
@app.route('/employee/dashboard')
def dashboard():
    if current_user.RoleID == 1 or current_user.RoleID == 2:
        categories = Category.query.limit(4)
        image_categories = url_for('static', filename=f'img/categories/cat-{id}')
        image_file = url_for('static', filename='img/profile_pics/' + current_user.image_file)
        user_id = current_user.id
        
        total_income = db.session.query(db.func.sum(OrderDetail.UnitPrice)).join(Order, 
        Order.OrderID == OrderDetail.OrderID).join(Product,Product.ProductID == OrderDetail.ProductID).filter(Product.CreatorID == user_id)
        
        total_order = db.session.query(db.func.count(Order.OrderID)).join(OrderDetail,Order.OrderID == OrderDetail.OrderID).join(Product,
        Product.ProductID == OrderDetail.ProductID).filter(Product.CreatorID == user_id)
        
        total_product_per_user = db.session.query(db.func.count(Product.ProductID)).filter(Product.CreatorID == user_id) 
        
        total_income_per_order = db.session.query(db.func.sum(OrderDetail.UnitPrice * OrderDetail.Quantity * 
        (1-OrderDetail.Discount)),Order.OrderDate).join(Order, OrderDetail.OrderID == Order.OrderID).join(Product,
        OrderDetail.ProductID == Product.ProductID).filter(Product.CreatorID == user_id).group_by(Order.OrderDate).order_by(Order.OrderDate)
        
        per_category_income = db.session.query(db.func.sum(OrderDetail.UnitPrice * OrderDetail.Quantity * 
        (1-OrderDetail.Discount)),Category.CategoryName).join(Product,OrderDetail.ProductID == Product.ProductID).join(Category,
        Product.CategoryId == Category.CategoryID).filter(Product.CreatorID == user_id).group_by(Category.CategoryName)
        
        transactions = db.session.query(db.func.sum(OrderDetail.UnitPrice * OrderDetail.Quantity * (1-OrderDetail.Discount)),Order.ShipName).join(Order,Order.OrderID == 
        OrderDetail.OrderID).join(Product,Product.ProductID == OrderDetail.ProductID).filter(Product.CreatorID == user_id).group_by(Order.ShipName).order_by(Order.OrderID.desc()).limit(7)

        last_order = db.session.query(Order.OrderID).join(OrderDetail,Order.OrderID == OrderDetail.OrderID).join(Product,
        Product.ProductID == OrderDetail.ProductID).filter(Product.CreatorID == user_id).order_by((Order.OrderID).desc()).first()

        average_shipping_day = db.session.query(db.func.avg((Order.ShippedDate - Order.OrderDate))).join(OrderDetail,Order.OrderID == OrderDetail.OrderID).join(Product,
        Product.ProductID == OrderDetail.ProductID).filter(Product.CreatorID == user_id)

        t_income = []
        t_order = []
        total_prd_per_user = []
        total_sales_list = []
        category_sales_list = []
        transactions_list = []
        average_ship_day = []
        last_order_id = []

        for i in average_shipping_day:
            average_ship_day.append(round(i[0]/86400000,2))

        for i in last_order:
            last_order_id.append(i)

        for amount,cat_name in per_category_income:
            category_sales_list.append(cat_name)
            category_sales_list.append(round(amount,2))
            
        category_sales_list = Convert(category_sales_list)
        
        for amount,customer_name in transactions:
            transactions_list.append((round(amount,2),customer_name))

        for amount,date in total_income_per_order:
            total_sales_list.append(date.strftime("%m-%d-%Y"))
            total_sales_list.append(amount)
    
        total_sales_dict = Convert(total_sales_list) 

        for i in total_product_per_user:
            total_prd_per_user.append(i[0])


        for t_o in total_order:
            t_order.append(t_o[0])

        for total_amount in total_income:
            t_income.append(float(total_amount[0]))
        
        return render_template('dashboard/index.html', total_income = json.dumps(t_income[0]),total_order = json.dumps(t_order[0]),image_file=image_file, 
        image_categories = image_categories, total_product = total_prd_per_user[0], total_sales_dict = total_sales_dict,categories=categories, 
        transactions_list = transactions_list, category_sales_list = category_sales_list,average_ship_day = average_ship_day[0],last_order_id = last_order_id[0])

    else:
        abort(403)

@login_required
@app.route('/employee/dashboard/products')
def dashboard_products():
    page = request.args.get('page',1,type=int)
    if current_user.RoleID == 1 or current_user.RoleID == 2:
        image_file = url_for('static', filename='img/profile_pics/' + current_user.image_file)
        user_id = current_user.id
        products = db.session.query(Product).filter(Product.CreatorID == user_id).paginate(page=page,per_page = 9)
        return render_template('dashboard/products.html',products = products,image_file = image_file)
    else:
        abort(403)


def save_picture_profile(form_picture):
    random_hex = secrets.token_hex(8)
    _ , f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img/profile_pics', picture_fn)
    
    output_size = (240,240)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn



@login_required
@app.route('/profile', methods = ['GET','POST'])
def profile():
    categories = Category.query.all()
    image_file = url_for('static', filename='img/profile_pics/' + current_user.image_file)
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture_profile(form.picture.data)
            current_user.image_file = picture_file

        current_user.name = form.name.data
        current_user.lastname = form.lastname.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.username = form.username.data
        current_user.email = form.email.data 
        db.session.commit()
        flash('Your profile has been updated!','success')
        return redirect(url_for('profile'))

    elif request.method == 'GET':
        form.name.data = current_user.name
        form.lastname.data = current_user.lastname
        form.phone.data = current_user.phone
        form.address.data = current_user.address
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template("profile.html",form=form,categories= categories,image_file = image_file)


@app.route("/contact")
def contact():
    categories = Category.query.all()
    return render_template("contact.html", categories = categories)



@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


# @app.route("/pics")
# def view_pics():
#     images = get_pics()
#     image_url = images[0]

#     return render_template('upload.html',image_url = image_url)



def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', 
    sender='noreply@virasoft.com',
    recipients=[user.email])

    msg.body = f""" To reset your password, visit the following link:
{url_for('reset_token',token = token, _external = True)}
    
If you did not make this request then ignore this email and no changes will be made.
"""
    mail.send(msg)

@app.route("/reset_password", methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title="Reset Password", form=form)


@app.route("/reset_password/<token>", methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token','warning')
        return redirect(url_for('reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been changed!','success')
        login_user(user)
        return redirect(url_for("login"))
    return render_template('reset_token.html', title="Reset Password", form=form)




admin = Admin(app)

admin.add_view(UserView(User,db.session))
admin.add_view(RoleView(Role,db.session))
admin.add_view(ModelView(Category,db.session))
admin.add_view(ModelView(Product,db.session))
admin.add_view(ModelView(Customer,db.session))
admin.add_view(ModelView(Employee,db.session))
admin.add_view(ModelView(Order,db.session))
admin.add_view(ModelView(OrderDetail,db.session))
admin.add_view(ModelView(Shipper,db.session))

