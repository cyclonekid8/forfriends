import os
import numpy as np
from sqlite3 import connect


from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

os.environ["API_KEY"]='pk_c35503acaa54408d88d5e2f553181a10' 

# Configure application
app = Flask(__name__)
if __name__=='__main__':
    app.debug=True
    app.run(host='localhost',port=5000)
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database


# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    dbcon =connect("finance.db")
    print("Opened database successfully");
    db=dbcon.cursor()
    user_id=session["user_id"]
    db.execute("SELECT symbol,name,shares,price,total,time FROM buys WHERE user_id=? AND shares!=0", str(user_id))
    rows=db.fetchall()
    db.execute("SELECT total FROM buys WHERE user_id=?",str(user_id))
    total=db.fetchall()
    totalval=0
    db.execute("SELECT cash FROM users WHERE id=?", str(user_id))
    cashval=db.fetchall()
    
    CASH=cashval[0][0]
    for i in total:
        totalval=totalval+i[0]
    totalval1="{:.2f}".format(totalval)
    TOTAL=totalval+CASH
    TOTAL1="{:.2f}".format(TOTAL)
    CASH1="{:.2f}".format(CASH)
    return render_template("index.html",rows=rows,totalval=totalval1,CASH=CASH1,TOTAL=TOTAL1)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method=="POST":
        symbol=request.form.get("symbol")
        if symbol.isalpha()==False:
            return apology("Invalid ticker symbol!")
        if len(symbol)!=4:
            return apology("Invalid ticket symbol!")
        if symbol==None:
            return apology("The input is blank")

        shares=request.form.get("shares")
        if shares.isdecimal()==False:
            return apology("Invalid input!1")
        shares=int(shares)

        if shares<0:
            return apology("The number of shares must be a positive integer!")
        user_id=session["user_id"]
        response=lookup(symbol)
        if response==None:
            return apology("The symbol does not exist!!")

        price=response['price']
        name=response['name']
        cost=round((price*shares),2)
        dbcon =connect("finance.db")
        print("Opened database successfully");
        db=dbcon.cursor()
        db.execute("SELECT cash FROM users WHERE id=?", str(user_id))
        cash=db.fetchall()
        cashvalue=cash[0][0]
        symbol=symbol.upper()
        if cost>cashvalue:
            return apology("You don't have enough cash!")
        else:
            amtleft=cashvalue-cost
            dbcon =connect("finance.db")
            print("Opened database successfully");
            db=dbcon.cursor()
            db.execute("UPDATE users SET cash=? WHERE id=?", (amtleft, user_id))
            dbcon.commit()
            db.execute("INSERT INTO buys (user_id,name,symbol,shares,price,total) VALUES(?,?,?,?,?,?)", (user_id,name,symbol,shares,price,cost))
            dbcon.commit()
            db.execute("INSERT INTO transactions (user_id,name,symbol,type,shares,price,total) VALUES(?,?,?,?,?,?,?)", (user_id,name,symbol,"buy",shares,price,cost))
            dbcon.commit()
            db.execute("SELECT symbol,name,shares,price,total,time FROM buys WHERE user_id=?", str(user_id))
            rows=db.fetchall()
            db.execute("SELECT total FROM buys WHERE user_id=?", str(user_id))
            total=db.fetchall()
            totalval=0
            print(total[0])
            for i in total:
                print(i)
                totalval=totalval+i[0]
            TOTAL=totalval+amtleft

        return redirect("/")
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    dbcon =connect("finance.db")
    print("Opened database successfully");
    db=dbcon.cursor()
    db.execute("SELECT * FROM transactions")
    response=db.fetchall()
    print(response)
    return render_template("history.html",rows=response)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        dbcon =connect("finance.db")
        print("Opened database successfully");
        db=dbcon.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        rows=db.fetchone()
        
        
        # Ensure username exists and password is correct
        if not check_password_hash(rows[2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method=="POST":
        symbol=request.form.get("symbol")
        if not symbol:
            return apology("No Symbol entered")
        if not symbol.isalpha():
            return apology("Invalid symbol!")
        if len(symbol)!=4:
            return apology("Invalid Ticker Symbol")
        return render_template("quoted.html",data=lookup(symbol),price=usd(lookup(symbol)["price"]))

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    dbcon =connect("finance.db")
    print("Opened database successfully");
    db=dbcon.cursor()
    users=db.execute("SELECT username FROM users")
    userlist=[]
    for i in users:
        userlist.append(i[0])

    if request.method=="POST":
        username=request.form.get("username")
        password1=request.form.get("password")
        password2=request.form.get("confirmation")

        if not username or username in userlist:
            return apology("Invalid Username!")

        if password1 != password2:
            return apology("Password Mismatch!")
        if not password1 or not password2:
            return apology("Please enter password again!")
        if password1.isalpha():
            return apology("Please use alphanumeric characters, 1 upper case letter and 1 symbol")
        if password1.isalnum():
            return apology("Please use symbols in your password!")
        res = any(char.isupper() for  char in password1)
        if not res:
            return apology("Please use at least 1 uppercase letter!")
        else:
            
            passwd=generate_password_hash(password1,method='pbkdf2:sha256',salt_length=8)
            db.execute("INSERT INTO users (username,hash) VALUES (?,?)", (username, passwd))
            dbcon.commit()
            
            return redirect("/login")

    return render_template("register.html",method=["GET","POST"])


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    stocklist=[]

    sharelist=[]
    user_id=session["user_id"]
    dbcon =connect("finance.db")
    print("Opened database successfully");
    db=dbcon.cursor()
    db.execute("SELECT symbol,name,shares,price,total FROM buys WHERE user_id=? and shares!=0", str(user_id))
    query=db.fetchall()
    db.execute("SELECT symbol,shares FROM buys WHERE user_id=? AND shares!=0", str(user_id))
    query2=db.fetchall()
    if request.method=="GET":

        stocklist=[]
        sharelist=[]

        for i in query2:
            stocklist.append(i[0])
            sharelist.append(i[1])
        return render_template("sell.html", stocklist=stocklist,sharelist=sharelist)
    if request.method=="POST":
        symbol=request.form.get("symbol")
        if symbol==None:
            return apology("You didn't select a stock!!")
        print(symbol)
        shares=int(request.form.get("shares"))
        stocklist=[]
        print(query2)

        limit=0
        for i in query2:
            if i[0]==symbol:
                limit=i[1]

        if shares>limit or shares<0:
            if shares<0:
                return apology("Input value is negative!!")
            return apology("You don't own enough shares!")
        price=lookup(symbol)["price"]
        name=lookup(symbol)["name"]
        cost=round(price*shares,2)
        dbcon =connect("finance.db")
        print("Opened database successfully");
        db=dbcon.cursor()
        db.execute("INSERT INTO sells (user_id,name,symbol,shares,price,total) VALUES(?,?,?,?,?,?)", (user_id,name,symbol,shares,price,cost))
        dbcon.commit()
        db.execute("INSERT INTO transactions (user_id,name,symbol,type,shares,price,total) VALUES (?,?,?,?,?,?,?)", (user_id,name,symbol,"sell",shares,price,cost))
        dbcon.commit()
        sharesleft=limit-shares

        db.execute("SELECT price FROM buys WHERE user_id=? AND symbol=?", (str(user_id), symbol))
        oldprice=db.fetchall()
        oldpriceentry=oldprice[0]
        newcost=oldpriceentry*sharesleft
        print(newcost)
        if newcost!= ():
            newcostt=newcost[0]
        else:
            newcostt=0
        db.execute("UPDATE buys SET shares=?,total=? WHERE user_id=? AND symbol=?",(sharesleft,newcostt,str(user_id),symbol))
        db.execute("SELECT cash FROM users WHERE id=?", str(user_id))
        prevcash=db.fetchall()
        currentcash=cost+prevcash[0][0]
        db.execute("UPDATE users SET cash=? WHERE id=?", (currentcash,str(user_id)))
        dbcon.commit()
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
