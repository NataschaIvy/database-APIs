import os, logging
from flask import Flask, request, Response
from flask import json
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from bson import json_util

logging.basicConfig(
    level=logging.DEBUG
)

#configure flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_URL']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#setup sql db
postgres = SQLAlchemy(app)
migrate  = Migrate(app, postgres)

#setup mongo
client = PyMongo(app, uri=f"mongodb://{os.environ['MONGO_USER']}:{os.environ['MONGO_PASSWORD']}@{os.environ['MONGO_URL']}:{os.environ['MONGO_PORT']}/{os.environ['MONGO_DB']}?authSource=admin")
mongo  = client.db

#SQL ORM class
class PostgresUser(postgres.Model):

    id          = postgres.Column(postgres.Integer, primary_key = True)    
    first_name  = postgres.Column(postgres.String(100))
    last_name   = postgres.Column(postgres.String(100))
    email       = postgres.Column(postgres.String(100)) 
    gender      = postgres.Column(postgres.String(100))
    ip_address  = postgres.Column(postgres.String(20))

    def as_dict(self):

        return { 
            "id":           self.id,
            "first_name":   self.first_name,
            "last_name":    self.last_name,
            "email" :       self.email,
            "gender" :      self.gender,
            "ip_address" :  self.ip_address
        }

    def __init__(self, data):

        self.id             = int(data[0])
        self.first_name     = data[1]
        self.last_name      = data[2]
        self.email          = data[3]
        self.gender         = data[4]
        self.ip_address     = data[5]        

        def __repr__(self):

            return f"<User {self.id}:{self.email}>"

#method to allow csv file upload
@app.route('/mongo/upload', methods = ['POST'])
def mongo_upload():

    file = request.files['file']    

    content = file.stream.readlines()

    for row in content[1:]:

        data = row.decode()[:-1].split(',')                                
        
        try:

            mongo.MongoUser.insert_one(
            { 
                'user_id'     : data[0],
                'first_name'  : data[1],
                'last_name'   : data[2],
                'email'       : data[3],
                'gender'      : data[4],
                'ip_address'  : data[5]                
            }) 

            logging.debug(f"added user {data[0]}")
        
        except Exception as e:

            logging.error(e)
            return jsonify({ "error" : f"error adding user {data[0]}"}), 400
    
    return jsonify({ "success" : f"{len(content) -1 } records loaded successfully"}), 200

#number of records in mongo db
@app.route("/mongo/count", methods = ['GET'])
def mongo_count():

    try:

        items = mongo.MongoUser.find()
        return jsonify({"count" : items.count()}), 200

    except Exception as e:

        logging.error(e)
        return jsonify({ "error" : "an unknown error occured"}), 500

#return a list of users
@app.route("/mongo/users", methods = ['GET'])
def mongo_users_get():

    result = []

    try:

        items = mongo.MongoUser.find()
        logging.debug(items)

        for item in items:

            logging.debug(item)
            result.append(item)

        return Response(json.dumps(result, default=json_util.default), mimetype='application/json'), 200

    except Exception as e:

        logging.error(e)
        return jsonify({ "error" : "an unknown error occured"}), 500        

#delete all rows
@app.route("/mongo/users", methods = ['DELETE'])
def mongo_users_delete():

    try:

        mongo.MongoUser.delete_many({})
        logging.debug("Deleted all users successfully")
        return jsonify({"success" : "all users deleted"}), 200

    except Exception as e:

        logging.error(e)
        return jsonify({ "error" : "an unknown error occured"}), 500 

#return specific row
@app.route("/mongo/users/<id>", methods = ['GET'])
def mongo_user_get(id):

    result = []

    try:

        items = mongo.MongoUser.find({"user_id": id})

        for item in items:

            result.append(item)

        if len(result) == 0:
            return jsonify({"error" : f"user {id} not found"})

        return Response(json.dumps(result, default=json_util.default), mimetype='application/json'), 200

    except Exception as e:

        logging.error(e)
        return jsonify({ "error" : "an unknown error occured"}), 500 

#delete specific row
@app.route("/mongo/users/<id>", methods = ['DELETE'])
def mongo_user_delete(id):

    try:

        item = mongo.MongoUser.delete_many({"user_id": id})
        logging.debug(item.raw_result)

        if item.raw_result['n'] is not 0:

            logging.debug(f"Deleted user {id}")
            return jsonify({"success" : f"user {id} deleted"}), 200

        return jsonify({"error" : f"user {id} not found"}), 400

    except Exception as e:

        logging.error(e)
        return jsonify({ "error" : "an unknown error occured"}), 500 

#method to allow csv file upload
@app.route('/postgres/upload', methods = ['POST'])
def postgres_upload():

    file = request.files['file']    

    content = file.stream.readlines()

    for row in content[1:]:

        data = row.decode()[:-1].split(',')                                
        
        try:

            item = PostgresUser(data)
            postgres.session.add(item)
            postgres.session.commit()
            logging.debug(f"Added user {data[0]}")            
        
        except Exception as e:

            postgres.session.rollback()
            logging.error(e)
            return jsonify({ "error" : f"error adding user {data[0]}" }), 400
    
    return jsonify({ "success" : f"{len(content) -1 } records loaded successfully"}), 200

#number of records in sql db
@app.route("/postgres/count", methods = ["GET"])
def postgres_count():
    
    try:

        users = PostgresUser.query.all()
        return jsonify({ "count" : len(users)}), 200

    except Exception as e:

        logging.error(e)
        return jsonify({ "error" : "an unknown error occured"}), 500    

#return a list of users
@app.route("/postgres/users", methods = ['GET'])
def postgres_users_get():
    
    result = []
    
    try:
    
        items = postgres.session.query(PostgresUser).all()        
    
        for item in items:                        
    
            result.append(item.as_dict())
    
    except Exception as e:

        logging.error(e)
        return jsonify({"error" : "unknown error occurred"}), 500

    return jsonify(result), 200

#delete all the users in the database
@app.route("/postgres/users", methods = ['DELETE'])
def postgres_users_delete():
    
    try:
    
        postgres.session.query(PostgresUser).delete()
        postgres.session.commit()
        logging.debug("Deleted all users successfully")
    
    except Exception as e:
    
        postgres.session.rollback()
        logging.error(e)
        return "unknown error", 500
    
    return "success", 200

#get user with the given id
@app.route("/postgres/users/<id>", methods = ['GET'])
def postgres_user_get(id):
    
    try:

        item = PostgresUser.query.get(int(id))

        if item is None:

            return jsonify({"error" : f"user {id} not found"}), 400

        return jsonify(item.as_dict()), 200

    except Exception as e:

        logging.error(e)
        return jsonify({ "error" : "an unknown error occured"}), 500 

#delete user with the given id
@app.route("/postgres/users/<id>", methods = ['DELETE'])
def postgres_user_delete(id):

    try:

        item = PostgresUser.query.get(int(id))

        if item is None:

            return jsonify({"error" : f"user {id} not found"}), 400

        postgres.session.query(PostgresUser).filter_by(id=int(id)).delete()
        postgres.session.commit()
        logging.debug(f"Deleted user {id}")
        return jsonify({"success" : f"user with id {id} deleted"}), 200

    except Exception as e:

        postgres.rollback()
        logging.error(e)
        return jsonify({ "error" : "an unknown error occured"}), 500

#entrypoint
if __name__ == '__main__':

   postgres.create_all()
   app.run(port = 80, debug = bool(os.environ['DEBUG']), host='0.0.0.0')
