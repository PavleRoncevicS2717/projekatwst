from flask import Flask, render_template, redirect, url_for, request, session
from pymongo import MongoClient
from flask_uploads import UploadSet, IMAGES, configure_uploads
from bson import ObjectId
import datetime	
import hashlib
import time

app = Flask(__name__)

photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static'
configure_uploads(app, photos)
client= MongoClient("mongodb+srv://test:test@cluster0-ssmbe.mongodb.net/test?retryWrites=true&w=majority")
app.config['SECRET_KEY'] = 'STRING NEKI'
db = client.get_database("db_projekat")
transakcije = db["transakcije"]
users = db["users"]
proizvodi = db["proizvodi"]

@app.route('/')
@app.route('/index')
def index():
	p = list(proizvodi.find())
	korisnik = {}
	korisnik['type'] = "test"
	if '_id' in session:
		korisnik = users.find_one({"_id": ObjectId(session["_id"])})
		return render_template('index.html',proizvodi = p,korisnik = korisnik,korisnici = users.find())
	return render_template('index.html',proizvodi=p,korisnik = korisnik,korisnici = users.find())

@app.route('/registracija',methods = ["POST","GET"])
def registracija():
	if request.method == 'GET':
		return render_template('registracija.html')
		
	hash_object = hashlib.sha256(request.form['password'].encode())
	password_hashed = hash_object.hexdigest()

	hash_object2 = hashlib.sha256(request.form['password2'].encode())
	password_hashed2 = hash_object2.hexdigest()

	if (password_hashed != password_hashed2):
		return 'Nije dobro ukucana sifra'

	if users.find_one({"ime": request.form['ime']}) is not None:
		return 'Korisnik vec postoji!'
	ime = request.form["ime"]
	prezime = request.form["prezime"]
	broj = request.form["broj"]
	email = request.form["email"]
	gender = request.form["gender"]
	pitanje = request.form["pitanje"]
	pare = 0
	tip = request.form["usertype"]
	
	unos = {
		"ime":ime,
		"prezime":prezime,
		"email":email,
		"broj":broj,
		"gender":gender,
		"password":password_hashed,
		"pare":pare,
		"tip":tip,
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
		session['tip'] = user['tip']
		
	return render_template('usplogin.html')
	
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

@app.route('/dodaj',methods = ["POST","GET"])
def dodaj():
	if session["tip"] != "admin":
		return "Niste ulogovani kao Administrator."
	if request.method == "GET":
		return render_template("dodaj.html")
	naziv = request.form["naziv"]
	if 'slika' in request.files:
			photos.save(request.files['slika'], 'img', request.form['naziv'] + '.png')
	cena = request.form['cena']
	naziv_slike = request.form["naziv"] + ".png"
	p = {
		"cena":cena,
		"naziv":naziv,
		'slika': "/static/img/" + naziv_slike
		
	}
	proizvodi.insert_one(p)
	return redirect(url_for('index'))

@app.route('/kupi',methods = ["POST"])
def kupi():
	user = users.find_one({"_id":ObjectId(session["_id"])})
	suma =0
	for x in user["korpa"]:
		proizvod = proizvodi.find_one({'_id':ObjectId(x)})
		
		suma += int(proizvod['cena'])
	if user['pare'] >= suma:
		pare = user['pare'] - suma
		
		kupovina = {
			'kupac_id':str(session['_id']),
			'proizvodi':user['korpa'],
			'time_stamp':time.strftime("%d-%m-%Y.%H:%M:%S")
		}
		transakcije.insert_one(kupovina)
		users.update_one({"_id": ObjectId(session['_id'])},{"$set":{'pare':pare,'korpa':[]}})

		return "Uspesno ste kupili dobru muziku"
	return "Nemate dovoljno para"

@app.route('/delete/<ObjectId>')
def delete(ObjectId):
	s = proizvodi.find_one({"_id":ObjectId})
	if s == None:
		return "Nema te ploce"
	proizvodi.delete_one({"_id":ObjectId})
	return redirect(url_for("index"))

@app.route('/update/<ObjectId>',methods = ["POST","GET"])
def update(indeks):
	
	if request.method == "GET":
		s = proizvodi.find_one({"index":indeks})
		if s == None:
			return "Ploca ne postoji."
		return render_template("update.html",student = s)
	else:
		naziv = request.form["naziv"] # request.form["name iz forme"] dohvatamo vrednost polja
		cena = request.form["cena"]
		
		p = {
		"cena":cena,
		"naziv":naziv,
		'slika': "/static/img/" + naziv_slike
		}

		proizvodi.update_one({"index":indeks},{"$set": s})
		return redirect(url_for('index'))

if __name__ == '__main__':
	app.run()