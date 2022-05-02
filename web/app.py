from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.BankAPI
users = db["Users"]

def UserExist(username):
    if users.find({"Username":username}).count()==0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status": "301"
                "msg": "Invalid Username"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('uft8'), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Own": 0,
            "Debt": 0
        })

        retJson = {
            "status": 200,
            "msg": "You succesfully signed up for the API"
        }
        return jsonify(retJson)

    #Helper functions
def verifyPw(username, password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw==hashed_pw):
        return True
    else:
        return False

def cashWithUser(username):
    cash = users.find({
        "Username": username
    })[0]["Own"]
    return cash

def debtWithUser(username):
    debt = users.find({
        "Username": username
    })[0]["Debt"]
    return debt

def generateReturnDictionary(status, msg):
    retJson = {
        "statu": status,
        "msg": msg
    }
    return retJson

#ErrorDictionary, True/False
def verifyCrendentials(username, password):
    if not UserExist(username):
        return generateReturnDictionary(301, "Invalid Username"), True

    correct_pw = verifyPw(username, password)

    if not correct_pw:
        return generateReturnDictionary(302, "Incorrect Password"), True

    return None, False

#Update account functions
def updateAccount(username, balance):
    users.update({
        "Username": username
    },{
        "$set":{
            "Own": balance
        }
    })

def updateDebt(username, balance):
    users.update({
        "Username": username,
    },{
        "$set":{
            "Debt": balance
        }
    })

class Add(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money    = postedData["amount"]

        retJson, error = verifyCrendentials(username, password)

        if error:
            return jsonify(retJson)

        if money<=0:
            return jsonify(generateReturnDictionary(304, "The money amount entered must be >0"))

        cash = cashWithUser(username)
        money-=1
        bank_cash = cashWithUser("BANK")
        updateAccount("BANK", bank_cash+1)
        updateAccount(username, cash+money)

        return jsonify(generateReturnDictionary(200, "Amount added succesfully to account"))

class Transfer(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        to       = postedData["to"]
        money    = postedData["amount"]

        retJson, error = verifyCrendentials(username, password)

        if error:
            return jsonify(retJson)

        cash = cashWithUser(username)
        if cash<=0:
            return jsonify(generateReturnDictionary(304, "You're out of money, please add or take a loan."))

        if not UserExist(to):
            return jsonify(generateReturnDictionary(301, "Receiver username is Invalid."))

        cash_from = cashWithUser(username)
        cash_to   = cashWithUser(to)
        bank_cash = cashWithUser("BANK")

        updateAccount("BANK", bank_cash+1)
        updateAccount(to, cash_to + money-1)
        updateAccount(username, cash_from-money)

        return jsonify(generateReturnDictionary(200, "Amount transfered succesfully."))

class Balance(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        retJson, error = verifyCrendentials(username, password)

        if error:
            return jsonify(retJson)

        retJson = users.find({
            "Username": username
        },{
            "Password": 0
            "_id": 0
        })[0]

        return jsonify(retJson)
