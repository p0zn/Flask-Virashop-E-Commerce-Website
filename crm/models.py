from pytz import timezone
import crm
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_admin.contrib.sqla import ModelView
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
import json


db = SQLAlchemy()



class Category(db.Model):
    __tablename__ = "Categories"
    CategoryID = db.Column(db.Integer, primary_key=True)
    CategoryName = db.Column(db.String(15), unique=False,nullable=False)
    Description = db.Column(db.String(255), unique=False, nullable=False)
    Products = db.relationship("Product", backref="Category", lazy=True)
    Picture = db.Column(db.String(255))



class Product(db.Model):
    __tablename__="Products"
    ProductID = db.Column(db.Integer,primary_key=True)
    CreatorID = db.Column(db.Integer,db.ForeignKey('User.id'),nullable=False)
    ProductName = db.Column(db.String(40), unique=False,nullable=False) 
    SupplierID = db.Column(db.Integer,unique=False,nullable=False)
    CategoryId = db.Column(db.Integer,db.ForeignKey('Categories.CategoryID'), nullable=False)
    QuantityPerUnit = db.Column(db.String(20), unique=False,nullable=False) 
    UnitPrice = db.Column(db.Float, unique=False, nullable=False)
    UnitsInStock = db.Column(db.Integer, unique=False, nullable=False)
    UnitsOnOrder = db.Column(db.Integer, unique=False, nullable=False)
    ReorderLevel = db.Column(db.Integer, unique=False, nullable=False)
    Discontinued = db.Column(db.Boolean, unique=False, nullable=False)
    Description = db.Column(db.String(255))
    image_1 = db.Column(db.String(150), nullable=False, default='default-product.jpg')
    image_2 = db.Column(db.String(150), nullable=False, default='default-product.jpg')
    image_3 = db.Column(db.String(150), nullable=False, default='default-product.jpg')
    comments = db.relationship("Comment", backref='product')
    



class Customer(db.Model):
    __tablename__ = "Customers"
    CustomerID = db.Column(db.Integer, primary_key=True)
    CompanyName = db.Column(db.String(40), unique = False,nullable=False)
    ContactName = db.Column(db.String(30), unique= False, nullable=False)
    ContactTitle = db.Column(db.String(30), unique = False, nullable=False)
    Address = db.Column(db.String(60), unique = False, nullable=False)
    City = db.Column(db.String(15), unique = False,nullable=False)
    Region = db.Column(db.String(15), unique= False, nullable=False)
    PostalCode = db.Column(db.String(10) , unique=False, nullable=False)
    Country = db.Column(db.String(15), unique = False, nullable = False)
    Phone = db.Column(db.String(24), unique=False, nullable=False)
    Fax = db.Column(db.String(24), unique = False, nullable=False)



class Employee(db.Model):
    __tablename__="Employees"
    EmployeeID = db.Column(db.Integer,primary_key=True) 
    LastName = db.Column(db.String(20), unique=False, nullable=False)
    FirstName = db.Column(db.String(10), unique=False, nullable=False)
    Title = db.Column(db.String(30) , unique=False, nullable=False)
    TitleOfCourtesy = db.Column(db.String(25), unique=False, nullable=False)
    BirthDate = db.Column(db.DateTime,unique=False, nullable=False)
    HireDate = db.Column(db.DateTime,unique=True, nullable=False)
    Address = db.Column(db.String(60), unique=False, nullable=False)
    City = db.Column(db.String(15), unique=False, nullable=False)
    Region = db.Column(db.String(15), unique = False, nullable=False)
    PostalCode = db.Column(db.String(15),unique=False, nullable=False)
    Country = db.Column(db.String(15),unique=False,nullable=False)
    HomePhone = db.Column(db.String(24),unique=False, nullable=False)
    Extension = db.Column(db.String(4),unique=False, nullable=False)
    Notes = db.Column(db.String,unique=False, nullable=False)
    ReportsTo = db.Column(db.Integer, unique = False , nullable=False)



class Order(db.Model):
    __tablename__ = "Orders"
    OrderID = db.Column(db.Integer, primary_key=True)
    CustomerID = db.Column(db.Integer,db.ForeignKey('Customers.CustomerID'), nullable = False)
    EmployeeID = db.Column(db.Integer,db.ForeignKey('Employees.EmployeeID'), nullable=False)
    OrderDate = db.Column(db.DateTime, unique = False, nullable = False)
    RequiredDate = db.Column(db.DateTime, unique = False, nullable = False)
    ShippedDate = db.Column(db.DateTime, unique = False , nullable = False)
    ShipVia = db.Column(db.Integer, unique = False, nullable = False)
    Freight = db.Column(db.Float, unique = False, nullable = False)
    ShipName = db.Column(db.String(40), unique = False,nullable = False)
    ShipAddress = db.Column(db.String(60), unique = False, nullable = False)
    ShipCity = db.Column(db.String(15), unique = False , nullable = False)
    ShipRegion = db.Column(db.String(15), unique = False, nullable = False)
    ShipPostalCode = db.Column(db.String(10), unique = False , nullable = False)
    ShipCountry = db.Column(db.String(15), unique = False, nullable = False)



class OrderDetail(db.Model):
    __tablename__ = "Order details"
    OrderID = db.Column(db.Integer, primary_key=True)
    # OrderID = db.Column(db.Integer, db.ForeignKey("Orders.OrderID"), nullable=False)
    ProductID = db.Column(db.Integer, db.ForeignKey("Products.ProductID"), nullable=False)
    UnitPrice = db.Column(db.Float(19,4), nullable=False, unique = False, default=1)
    Quantity = db.Column(db.Integer, nullable=False, unique = False, default=1)
    Discount = db.Column(db.Float, nullable=False, unique = False, default=0)



class Shipper(db.Model):
    __tablename__ = "Shippers"
    ShipperID = db.Column(db.Integer, primary_key=True)
    CompanyName = db.Column(db.String(40), nullable=False , unique = False)
    Phone = db.Column(db.String(24), nullable=False, unique = False)

    def __repr__(self):
        return '<Company Name %r>' % self.CompanyName



class Supplier(db.Model):
    __tablename__ = "Suppliers"
    SupplierID = db.Column(db.Integer, primary_key=True)
    CompanyName = db.Column(db.String(40), nullable=False , unique = False)
    ContactName = db.Column(db.String(30), unique= False, nullable=False)
    ContactTitle = db.Column(db.String(30), unique = False, nullable=False)
    Address = db.Column(db.String(60), unique = False, nullable=False)
    City = db.Column(db.String(15), unique = False,nullable=False)
    Region = db.Column(db.String(15), unique= False, nullable=False)
    PostalCode = db.Column(db.String(10) , unique=False, nullable=False)
    Country = db.Column(db.String(15), unique = False, nullable = False)
    Phone = db.Column(db.String(24), unique=False, nullable=False)
    Fax = db.Column(db.String(24), unique = False, nullable=False)

    def __repr__(self):
        return '<Company Name %r>' % self.CompanyName



class User(db.Model,UserMixin):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    lastname = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(11), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    RoleID = db.Column(db.Integer,db.ForeignKey("Roles.roleID"), default=0)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    products = db.relationship("Product", backref="user.id", lazy=True, passive_deletes = True)
    comments = db.relationship("Comment", backref="user", lazy=True, passive_deletes = True)
    


    def get_reset_token(self,expires_sec = 1800):
        s = Serializer(crm.app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(crm.app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None

        return User.query.get(user_id)

    def __repr__(self):
        return '<User %r>' % self.username

class UserView(ModelView):
    form_columns = ['id','username','password','email','RoleID','image_file']


class Role(db.Model):
    __tablename__ = "Roles"
    roleID = db.Column(db.Integer, primary_key=True, default=0) 
    role = db.Column(db.String(255))

    def __repr__(self):
        return '<Roles %r>' % self.role 

class RoleView(ModelView):
    form_columns = ['roleID','role']


class Comment(db.Model):
    __tablename__ = "Comment"
    id = db.Column(db.Integer, primary_key=True)
    comment_text = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default = db.func.now())
    author = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.ProductID'), nullable=False)
    rating = db.Column(db.Integer)


class JsonEcodedDict(db.TypeDecorator):
    impl = db.Text

    def process_bind_param(self,value,dialect):
        if value is None:
            return '{}'

        else:
            return json.dumps(value)
    
    def process_result_value(self,value,dialect):
        if value is None:
            return {}
        
        else: 
            return json.loads(value)


class Cargo(db.Model):
    __tablename__ = "Cargo"
    status_id = db.Column(db.Integer, primary_key=True, default=0) 
    cargo_status = db.Column(db.String(255))
    

class Newsletter(db.Model):
    __tablename__ = "Newsletter"
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(255))


class CustomerOrder(db.Model):
    __tablename__ = "Customerorders"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    lastname = db.Column(db.String(40), nullable=False)
    address1 = db.Column(db.String(200), nullable=False)
    address2 = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(18), nullable=False)
    city = db.Column(db.String(40), nullable=False)
    state = db.Column(db.String(20), nullable=False)
    zip = db.Column(db.Integer, nullable=False)
    invoice = db.Column(db.String(20),unique=True, nullable=False)  
    order_status = db.Column(db.Integer,db.ForeignKey("Cargo.status_id"), default=0)  
    customer_id = db.Column(db.Integer,unique=False, nullable=False) 
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tracking_number = db.Column(db.String(20), nullable=True, default="not yet shipped")
    orders = db.Column(JsonEcodedDict)
    cache_ok = True


    def __repr__(self):
        return '<CustomerOrder %r>' % self.id

