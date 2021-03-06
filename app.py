from flask.helpers import make_response
from pymongo import MongoClient
import jwt
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'
client = MongoClient('localhost', 27017)
db = client.week_one


## HTML 화면 보여주기
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])  # 로그인 확인

        return render_template('main.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()  # 인코딩
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/search', methods=['GET']) # /search로 키워드를 받아 식당 이름과 일치 결과를 DB에서 찾아옴
def search_get():
   doc = [] # 검색을 마친 자료가 들어갈 배열
   store_receive = request.args.get('store_give') # Ajax에서 store_give로 보낸 데이터를 받음
   stores = list(db.restaurants.find({},{'_id':False})) # 식당의 전체 목록을 stores 변수로 받음
   for store in stores:
    if store_receive in store['name']: # store_receive로 받은 검색어를 찾아봅니다.
         doc.append(store) # 일치하는 식당을 doc 배열에 삽입
   search_list = {'search_list':doc} # API로 전달할 수 있는 자료에 배열 형태는 없으므로, 딕셔너리로 형태로 저장
   return jsonify({'search_list':search_list, 'msg':'검색 완료!'})

@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})





# 등록하기(POST) API
@app.route('/post', methods=['POST'])
def post_place():
    #img_url_receive = request.form['img_url_give']
    name_receive = request.form['name_give']
    type_receive = request.form['type_give']
    continent_receive = request.form['continent_give']
    star_receive = request.form['star_give']
    review_receive = request.form['review_give']
    file = request.files["file_give"]

    extension = file.filename.split('.')[-1]
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    filename = f'file-{mytime}'
    save_to = f'static/{filename}.{extension}'
    file.save(save_to)

    doc = {
        'name': name_receive,
        'type': type_receive,
        'continent': continent_receive,
        'star': star_receive,
        'review': review_receive,
        'file': f'{filename}.{extension}'
        #'img-url': img_url_receive,
    }

    db.restaurants.insert_one(doc)
    return jsonify({'msg': '등록 완료!'})


# # 검색어로 레스토랑 보기
# @app.route('/post', methods=['GET'])
# def search_place():
#     word_receive = request.form['word_give']
#     place = db.restaurants.find_one({'name': word_receive}, {'_id': False})
#     return jsonify({'msg': 'Search Complete', 'place': place})

# 주문 목록보기(Read) API
# @app.route('/places', methods=['GET'])
# def view_places():

#     places = list(db.restaurants.find({}, {'_id': False}))

#     return jsonify({'places': places})

@app.route('/<continent>')
def continent(continent):
    if continent == "ALL":
        places = list(db.restaurants.find({}, {'_id': False}))
    else:
        places = list(db.restaurants.find({'continent': continent}, {'_id': False}))
    return render_template('main.html', places=places)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

