#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3308,
                       user='root',
                       password='',
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth(): #done
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST']) 
def registerAuth(): #done
    if request.method == 'POST':
        #grabs information from the forms
        username = request.form['username']
        password = request.form['password']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']

        #cursor used to send queries
        cursor = conn.cursor()
        #executes query
        query = 'SELECT * FROM Person WHERE username = %s'
        cursor.execute(query, (username))
        #stores the results in a variable
        data = cursor.fetchall()
        #use fetchall() if you are expecting more than 1 data row
        error = None
        if(data):
            #If the previous query returns data, then user exists
            error = "This user already exists"
            return render_template('register.html', error = error)
        else:
            ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
            cursor.execute(ins, (username, password, firstName, lastName, email))
            conn.commit()
            cursor.close()
            return render_template('index.html')
    else:
        return render_template('register.html')

@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT firstName FROM Person WHERE username = %s'
    cursor.execute(query, (user))
    data = cursor.fetchone()
    name = data["firstName"]
    cursor.close()
    return render_template('home.html', username=name) #posts=data)

'''
@app.route('/select_blogger')
def select_blogger():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM blog'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)
'''
'''
@app.route("/unFollow")
def unFollow():
    try:
        username = session['username']
    except:
        return render_template('index.html')
    cursor=conn.cursor()
    query="DELETE FROM FOLLOW where follower=%s and followee=%s"
    cursor.execute(query,(username,toAccept))
    cursor.close()
    return redirect(url_for('manageFollowee'))

@app.route('/imageInformation')
    def imageInfo():
    imageInfo = "SELECT * FROM photo WHERE photoID = %s"
    with connection.cursor() as cursor:
        cursor.execute(imageInfo, photoID)
    return cursor.fetchone()

'''
'''
@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)
'''

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

@app.route('/post_photo_home', methods = ['GET', 'POST'])
def post_photo_home():
    username = session["username"]
    cursor = conn.cursor();
    friendGroup = "SELECT groupName FROM belongto NATURAL JOIN friendgroup WHERE username = %s or groupCreator = %s"
    cursor.execute(friendGroup, (username,username))
    groups = [item['groupName'] for item in cursor.fetchall()]
    cursor.close()
    return render_template('post_photo.html', groups=groups)

@app.route('/post_photo', methods = ['GET','POST'])
def post_photo():
    
    if request.form.getlist("allFollowers") == ["on"]: #on = checked, off = not
        #checked -> private -> allFollowers == 0
        private_public = 0 # means that it is checked, therefore false therefore  private, 0 == false
    else:
        private_public = 1 # not checked, automatically public to allFollowers, 1 == true

    username = session["username"]
    location = request.form["location"]
    caption = request.form["caption"]
    cursor = conn.cursor();
    
    query = "INSERT INTO Photo (postingDate,filePath, allFollowers, caption, poster) VALUES (CURRENT_TIMESTAMP,%s,%s,%s,%s)"
    cursor.execute(query,(location, private_public, caption, username))

    if (private_public == 0): # if it's private
        group_name_group_creator = "SELECT groupCreator,groupName FROM friendGroup NATURAL JOIN belongTo WHERE username = %s or groupCreator = %s"
        cursor.execute(group_name_group_creator, (username,username))
        result = cursor.fetchall()

        group_selected = request.form.getlist("groups")
        for i in range(len(group_selected)):
            for item in result:
                if item["groupName"] == group_selected[i]:
                    sharing = "INSERT INTO SharedWith VALUES (LAST_INSERT_ID(),%s,%s)"
                    cursor.execute(sharing, (group_selected[i],item["groupCreator"]))  

    cursor.close()
    return render_template("post_photo_finish.html")

@app.route('/post_photo_finish')
def post_photo_finish():
    return render_template("home.html")

@app.route('/add_friend_group_home', methods = ['GET', 'POST'])
def add_friend_group_home():
    return render_template("friend_group.html")

@app.route('/add_friend_group', methods = ['GET', 'POST'])
def add_friend_group():
    user = session["username"]
    groupName = request.form["groupName"]
    description = request.form["description"]

    cursor = conn.cursor();
    check = "SELECT * FROM FriendGroup WHERE groupName = %s AND groupCreator = %s"
    cursor.execute(check, (groupName,user))
    data = cursor.fetchone()
    error = None
    if (data):
        error = "This friend group already exists"
        return render_template("friend_group.html", error = error)
    else:
        query = "INSERT INTO FriendGroup VALUES (%s, %s, %s)"
        belong_to_query = "INSERT INTO BelongTo VALUES (%s,%s,%s)"
        cursor.execute(query, (groupName, user, description))
        cursor.execute(belong_to_query, (user,groupName,user))
    cursor.close()
    return render_template("post_photo_finish.html")

@app.route('/add_friend_group_finish')
def add_friend_group_finish():
    return render_template("home.html")
    
'''
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    blog = request.form['blog']
    query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
    cursor.execute(query, (blog, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))
'''
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = False)
