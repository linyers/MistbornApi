from flask import Flask, Response, request, render_template, jsonify, redirect, url_for
import pymongo
from bson.objectid import ObjectId
from bson.json_util import dumps
import os
import json
import re
from decouple import config

client = pymongo.MongoClient(config('MONGODB_URI'))
db = client["MistbornApi"]
app = Flask(__name__)
app.config['API_KEY'] = config('SECRET_KEY')

@app.route('/api', methods = ['GET'])
def apimain():
    colections = {
        "characters": "/api/v1.0/characters",
        "locations": "/api/v1.0/locations",
        "magic": "/api/v1.0/magic"
    }
    return Response(dumps(colections), mimetype='application/json')

@app.route('/api/v1.0/characters', methods = ['GET'])
def characters():
    character = db.characters.find()
    return Response(dumps(character), mimetype='application/json')

@app.route('/api/v1.0/characters/<_id>', methods = ['GET'])
def character_id(_id):
    if "," in _id:
        _id = _id.split(",")
        _id = list(map(int, _id))
        character = db.characters.find({'_id':{"$in":_id}})
    else:
        _id = list(map(int, _id))
        character = db.characters.find({'_id':_id})
    return Response(dumps(character), mimetype='application/json')

@app.route('/api/v1.0/characters/', methods = ['GET'])
def character_query():
    name = ""
    ethn = ""
    relig = ""
    if request.args.get('name') != None:
        name = request.args.get('name').capitalize()
    if request.args.get('ethn') != None:
        ethn = request.args.get('ethn').capitalize()
    if request.args.get('relig') != None:
        relig = request.args.get('relig').capitalize()
    query = {
        'name':{"$regex":name},
        'ethnicity':{"$regex":ethn},
        'religion':{"$regex":relig}
    }
    character = db.characters.find(query)
    return Response(dumps(character), mimetype='application/json')

#POSTS
@app.route('/api/v1.0/characters', methods = ['POST'])
def create_character():
    api_key = request.args.get('api_key')
    if api_key != app.config['API_KEY']:
        return jsonify({'error': 'API key inválida'})
    else:
        _id = int(db.characters.count_documents({}) + 1)
        name= request.json['name']
        aliases= request.json['aliases']
        family= request.json['family']
        born = request.json['born']
        died = request.json['died']
        abilities = request.json['abilities']
        profession = request.json['profession']
        religion = request.json['religion']
        titles = request.json['titles']
        groups = request.json['groups']
        birthplace = request.json['birthplace']
        residence = request.json['residence']
        ethnicity = request.json['ethnicity']
        featured_in = request.json['featured_in']
        image = request.json['image']
        coppermind = "https://coppermind.net/wiki/" + name
        world = request.json['world']

        charac = {'_id': _id,'name':name,'aliases':aliases,'family':family,'born':born, 'died':died,'abilities':abilities,'profession':profession,'religion':religion,'titles':titles,'groups':groups,'birthplace':birthplace,'residence':residence,'ethnicity':ethnicity,'featured_in':featured_in,'image':image,'world':world ,'coppermind':coppermind}
        db.characters.insert_one(charac)

        url = '/api/v1.0/characters/' + name
        return redirect(url)

#PATCH
@app.route('/api/v1.0/characters/<name>', methods = ['PATCH'])
def update_character(name):
    api_key = request.args.get('api_key')
    if api_key != app.config['API_KEY']:
        return jsonify({'error': 'API key inválida'})
    else:
        query = request.json['query']
        db.characters.update_one({'name':name}, {'$set':query})
        url = '/api/v1.0/characters/' + name
        return redirect(url)

@app.route('/api/v1.0/characters/<name>', methods = ['DELETE'])
def delete_character(name):
    api_key = request.args.get('api_key')
    if api_key != app.config['API_KEY']:
        return jsonify({'error': 'API key inválida'})
    else:
        db.characters.delete_one({"name":name})
    return redirect('/api/v1.0/characters')

@app.route('/', methods = ['GET'])
def main():
    pipeline = [
        {'$match': {'image': {'$ne': ""}}},
        {'$sample': {'size': 6}}
    ]
    result = db.characters.aggregate(pipeline)
    datos = list()
    for doc in result:
        name = doc["name"]
        url_name = "/api/v1.0/characters/" + name
        featured = ", ".join(doc["featured_in"][:3])
        abilities = "Any"
        if len(doc["featured_in"]) > 3:
            featured = featured + ', other'
        if len(doc["abilities"]) > 0:
            abilities = str(doc["abilities"][0])
            if len(doc["abilities"]) > 1:
                abilities = abilities + ', other'
        image = doc["image"]
        coppermind = doc["coppermind"]
        datos.append({'name':name, 'url_name':url_name, 'image':image, 'featured':featured.replace('"', ""), 'coppermind':coppermind, 'abilities':abilities})
    num_char = db.characters.count_documents({})
    return render_template('main.html', datos=datos, num_char=num_char)

@app.route('/about', methods = ['GET'])
def about():
    num_char = db.characters.count_documents({})
    return render_template('about.html', title='About', num_char=num_char)

@app.route('/documentation', methods = ['GET'])
def docs():
    num_char = db.characters.count_documents({})
    return render_template('docs.html', title='Documentation', num_char=num_char)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)