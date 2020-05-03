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
    visible_photo_query = 'SELECT filePath, pID FROM Photo NATURAL JOIN follow WHERE poster = %s OR poster = followee and follower = %s'
    cursor.execute(visible_photo_query, (user, user))
    photos = [item for item in cursor.fetchall()]
    photos.reverse()
    second_photo_query = "SELECT filePath, pID FROM sharedwith NATURAL JOIN belongto NATURAL JOIN photo WHERE username = %s or groupCreator = %s GROUP BY pID"
    cursor.execute(second_photo_query, (user,user))
    second_photos = [item for item in cursor.fetchall()]
    for i in range(len(photos)):
        if photos[i] not in second_photos:
            second_photos.append(photos[i])
    new_photo = sorted(second_photos, key=lambda k: k['pID']) #order by pID reverse, since pID is a determinant of chronological order
    new_photo.reverse()
    print(new_photo)
    cursor.close()
    return render_template('home.html', username=name, photos = new_photo) #posts=data)

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

    if (private_public == 0):
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
    username = session["username"]
    cursor = conn.cursor();
    friendGroup = "SELECT groupName FROM belongto NATURAL JOIN friendgroup WHERE username = %s or groupCreator = %s"
    cursor.execute(friendGroup, (username,username))
    groups = [item['groupName'] for item in cursor.fetchall()]
    cursor.close()
    return render_template("friend_group.html", groups=groups)

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

@app.route('/leave_friend_group', methods = ['GET', 'POST'])
def leave_friend_group():
    cursor = conn.cursor();
    group_selected = request.form.getlist("groups")
    for i in range(len(group_selected)):
        for item in result:
            if item["groupName"] == group_selected[i]:
                sharing = "INSERT INTO SharedWith VALUES (LAST_INSERT_ID(),%s,%s)"
                cursor.execute(sharing, (group_selected[i],item["groupCreator"])) 
    return render_template("post_photo_finish.html")

'''
@app.route('/add_friend_group_finish') #dont know if i need this
def add_friend_group_finish():
    return render_template("home.html")
'''

@app.route('/follow_home', methods = ['GET', 'POST'])
def follow_home():
    user = session["username"]
    cursor = conn.cursor();
    following_query = "SELECT DISTINCT followee FROM follow WHERE followStatus = 1 AND follower = %s"
    cursor.execute(following_query, (user))
    following = [item['followee'] for item in cursor.fetchall()]
    cursor.close()      
    return render_template("follow.html", following = following)

@app.route('/follow', methods = ['GET', 'POST'])
def follow():
    user = session["username"]
    username = request.form["username"]
    cursor = conn.cursor();

    #request to follow
    query = "INSERT INTO follow VALUES (%s, %s, 0)" #user is the follower, which is the first, username is the followee.
    cursor.execute(query, (user,username))
    cursor.close()
    return render_template("post_photo_finish.html")
    
@app.route('/unfollow', methods = ['GET', 'POST']) #works
def unfollow():
    user = session["username"]
    following_selected = request.form.getlist("following")

    cursor = conn.cursor();
    for i in range(len(following_selected)):
        remove = "DELETE FROM Follow WHERE follower = %s AND followee = %s"
        cursor.execute(remove,(user,following_selected[i]))
    cursor.close();
    return render_template("post_photo_finish.html")

@app.route('/follower_home', methods = ['GET', 'POST'])
def followers_home():
    user = session["username"]
    cursor = conn.cursor();
    following_query = "SELECT DISTINCT follower FROM follow WHERE followStatus = 0 AND followee = %s"
    cursor.execute(following_query, (user))
    followers = [item['follower'] for item in cursor.fetchall()]
    cursor.close()      
    return render_template("followers.html", followers = followers)

@app.route('/follower', methods = ['GET', 'POST'])
def followers():
    user = session["username"]
    followers = request.form.getlist("followers")
    print(followers)
    cursor = conn.cursor();
    for i in range(len(followers)):
        update = "UPDATE follow SET followStatus = 1 WHERE followee = %s AND follower = %s"
        cursor.execute(update,(user,followers[i]))
    cursor.close();
    return render_template("post_photo_finish.html")

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
