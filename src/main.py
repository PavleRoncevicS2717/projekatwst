from flask import Flask, render_template, redirect, url_for, request, session
from pymongo import MongoClient
from flask_uploads import UploadSet, IMAGES, configure_uploads
from bson import ObjectId
import datetime	
import hashlib
import time


photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static'
configure_uploads(app, photos)
client= MongoClient()
app.config['SECRET_KEY'] = 'STRING NEKI'
db = client.get_database("db_projekat")
users = db["users"]
proizvodi = db["proizvodi"]

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for)

@app.route('/registracija',methods = ["POST","GET"])
def registracija():
	if request.method == 'GET':
		return render_template('registracija.html')
		
	hash_object = hashlib.sha256(request.form['password'].encode())
	password_hashed = hash_object.hexdigest()

	if users.find_one({"ime": request.form['ime']}) is not None:
		return 'Korisnik vec postoji!'
	ime = request.form["ime"]
	prezime = request.form["prezime"]
	broj = request.form["broj"]
	email = request.form["email"]
	gender = request.form["gender"]
	pitanje = request.form["pitanje"]
	pare = 0
	
	unos = {
		"ime":ime,
		"prezime":prezime,
		"email":email,
		"broj":broj,
		"gender":gender,
		"password":password_hashed,
		"pare":pare,
        "pitanje":pitanje,
		'created': time.strftime("%d-%m-%Y.%H:%M:%S"),
		"korpa":[]
	}
	users.insert_one(unos)
	return redirect(url_for('login'))

@app.route('/login',methods =["GET","POST"])
def login():
	if '_id' in session:
		return "Vec ste ulogovani"
	if request.method == 'GET':
		return render_template('login.html')
	else:
		hash_object = hashlib.sha256(request.form['password'].encode())
		password_hashed = hash_object.hexdigest()
		user = users.find_one({'email':request.form['email'], 'password':password_hashed})
		if user is None:
			return 'Pogresan email ili password!'
		session['_id'] = str(user['_id'])
	return redirect(url_for('index'))
@app.route('/logout')
def logout():
	if "_id" in session:
		session.pop('_id',None)
		return redirect(url_for('login'))
	return redirect(url_for('login'))
@app.route('/dodaj_u_korpu',methods = ["POST"])
def dodaj_u_korpu():
	p = proizvodi.find_one({'_id': ObjectId(request.form['prodavac'])})
	korisnik = users.find_one({'_id':ObjectId(session['_id'])})
	korpa = korisnik["korpa"]
	korpa.append(p['_id'])
	users.update_one({'_id':ObjectId(session['_id'])},{"$set":{"korpa":korpa}})
	return redirect(url_for('index'))