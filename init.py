#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import os

#Initialize the app from Flask
app = Flask(__name__, static_url_path ="", static_folder ="static")


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

    #get photo of all people user followed
    visible_photo_query = 'SELECT filePath, pID, firstName, lastName, postingDate, caption FROM follow NATURAL join photo NATURAL JOIN person WHERE pID IN (SELECT pID FROM follow NATURAL JOIN photo WHERE follower = %s AND poster = followee AND username = poster AND followstatus = 1) OR pID IN (SELECT pID FROM photo WHERE poster = %s AND poster = username AND followee = poster) GROUP BY pID'
    cursor.execute(visible_photo_query, (user,user))
    photos = [item for item in cursor.fetchall()]
    photos.reverse()

    #get photo of everything shared
    second_photo_query = "SELECT filePath, pID, firstName, lastName, postingDate, caption FROM sharedwith AS s NATURAL JOIN belongto AS b NATURAL JOIN photo JOIN person AS p ON (p.username = s.groupCreator) WHERE b.username = %s"
    cursor.execute(second_photo_query, (user))
    second_photos = [item for item in cursor.fetchall()]

    #combine list
    for i in range(len(photos)):
        if photos[i] not in second_photos:
            second_photos.append(photos[i])
    new_photo = sorted(second_photos, key=lambda k: k['pID']) #order by pID reverse, since pID is a determinant of chronological order
    new_photo.reverse()

    tag = "SELECT username,pID FROM tag WHERE pID = %s AND tagStatus = 1"

    tags = []

    #find all photos with tagged in the list of combined photos
    for item in new_photo:
        #adding a tag to the dic to prepare for tag append later
        item["tag"] = []
        cursor.execute(tag,(item["pID"]))
        if tags == []:
            tags = [item for item in cursor.fetchall()]
        else:
            tags += [item for item in cursor.fetchall()]

    #appending tag
    for item in new_photo:
        for item_2 in tags:
            if item["pID"] == item_2["pID"]:
                item["tag"].append(item_2["username"])

    heart_reac = "SELECT username,pID,emoji, comment FROM reactto WHERE pID = %s"

    reacts = []

    for item in new_photo:
        #adding a tag to the dic to prepare for tag append later
        item["react"] = []
        cursor.execute(heart_reac,(item["pID"]))
        if reacts == []:
            reacts = [item for item in cursor.fetchall()]
        else:
            reacts += [item for item in cursor.fetchall()]

    #find all photos with reactto
    for item in new_photo:
        for item_2 in reacts:
            if item["pID"] == item_2["pID"]:
                item["react"].append(item_2["username"])
                if not item_2["emoji"]:
                    item["react"].append("")
                else:
                    item["react"].append(item_2["emoji"])
                if not item_2["comment"]:
                    item["react"].append("")
                else:
                    item["react"].append(item_2["comment"])
    cursor.close()
    return render_template('home.html', username=name, photos = new_photo)

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

    #show all groups that user created
    user_group = "SELECT groupName FROM friendgroup WHERE groupCreator = %s"
    cursor.execute(user_group, (username))
    personal_group = [item['groupName'] for item in cursor.fetchall()]

    #select all group to be leaving on later, whether it's user's group or someone added user to it
    friendGroup = "SELECT DISTINCT groupName, groupCreator FROM belongto NATURAL JOIN friendgroup WHERE username = %s or groupCreator = %s"
    cursor.execute(friendGroup, (username,username))
    groups = cursor.fetchall() #item['groupName'] for item in cursor.fetchall()]

    cursor.close()
    return render_template("friend_group.html", groups=groups, personal_group=personal_group)

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

@app.route('/add_friend', methods = ['GET', 'POST']) #done
def add_friend():
    cursor = conn.cursor();
    user = session["username"]
    username = request.form["username"]
    group_selected = request.form.getlist("personal_group")

    for i in range(len(group_selected)):
        add = "INSERT INTO belongto (username,groupName,groupCreator) VALUES (%s, %s, %s)"
        cursor.execute(add,(username,group_selected[i], user))
    cursor.close()
    return render_template("post_photo_finish.html")
    
@app.route('/leave_friend_group', methods = ['GET', 'POST'])
def leave_friend_group():
    user = session["username"]
    cursor = conn.cursor();

    #grab all groups that user created to check later on
    creator_check = "SELECT groupName, groupCreator FROM friendgroup WHERE groupCreator = %s"
    cursor.execute(creator_check,(user))
    creator_groups = cursor.fetchall()

    #grabbing the group selected and converting them from string dic to actual dic using json
    group_selected = request.form.getlist("groups")
    for i in range(len(group_selected)):
        json_acceptable_string = group_selected[i].replace("'", "\"")
        group_selected[i] = json.loads(json_acceptable_string)

    #query to be used later
    leave_group = "DELETE FROM belongto WHERE userName = %s AND groupName = %s"
    belongto_delete = "DELETE FROM belongto WHERE groupCreator = %s AND groupName = %s"
    sharedwith_delete = "DELETE FROM sharedwith WHERE groupCreator = %s AND groupName = %s"
    friendgroup_delete = "DELETE FROM friendgroup WHERE groupCreator = %s AND groupName = %s"
    
    for item in group_selected:
        #check to see if he's deleting his own created group
        if item in creator_groups: 
            cursor.execute(belongto_delete, (user,item["groupName"])) 
            cursor.execute(sharedwith_delete, (user,item["groupName"])) #delete by groupCreator
            cursor.execute(friendgroup_delete, (user,item["groupName"]))

        #else
        else:
            cursor.execute(leave_group, (user,item["groupName"]))

    cursor.close()
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
    cursor.close()
    return render_template("post_photo_finish.html")

@app.route('/follower_home', methods = ['GET', 'POST'])
def followers_home():
    user = session["username"]
    cursor = conn.cursor();
    following_query = "SELECT DISTINCT follower FROM follow WHERE followStatus = 0 AND followee = %s" #displays non follower
    cursor.execute(following_query, (user))
    followers = [item['follower'] for item in cursor.fetchall()]
    current_followers_query = "SELECT DISTINCT follower FROM follow WHERE followStatus = 1 AND followee = %s" #displays followers
    cursor.execute(current_followers_query, (user))
    current_followers = [item['follower'] for item in cursor.fetchall()]
    cursor.close()      
    return render_template("followers.html", followers = followers, current_followers = current_followers)

@app.route('/follower', methods = ['GET', 'POST'])
def followers():
    user = session["username"]
    followers = request.form.getlist("followers")
    cursor = conn.cursor();
    for i in range(len(followers)):
        update = "UPDATE follow SET followStatus = 1 WHERE followee = %s AND follower = %s"
        cursor.execute(update,(user,followers[i]))
    cursor.close();
    return render_template("post_photo_finish.html")

@app.route('/remove_follower', methods = ['GET', 'POST'])
def remove_followers():
    user = session["username"]
    followers = request.form.getlist("followers")
    cursor = conn.cursor();
    for i in range(len(followers)):
        update = "DELETE FROM follow WHERE followee = %s AND follower = %s"
        cursor.execute(update,(user,followers[i]))
    cursor.close()
    return render_template("post_photo_finish.html")
  
@app.route("/block")
def block():
    try:
        username = session['username']
    except:
        return render_template('index.html')
    
    blocking = request.args['blocking']
    cursor=conn.cursor()
    query="INSERT INTO finstagram.block(blocker,blockee) VALUES(%s,%s)"
    cursor.execute(query,(username,blocking))
    conn.commit()
    cursor.close()
    # print(username,toblock)
    return redirect(url_for('manageBlock'))
  
@app.route("/manageBlock")
def manageBlock():
    try:
        username = session['username']
    except:
        return render_template('index.html')
    cursor=conn.cursor()
    query="SELECT username From (SELECT blockee FROM block WHERE blocker = %s) AS notseen RIGHT JOIN Person on notseen.blockee = Person.username WHERE blockee is Null and username != %s"
    cursor.execute(query,(username,username))
    data=cursor.fetchall()
    cursor.close()
    return render_template("block.html",persons=data)

@app.route('/delete_account')
def delete_account():
    user = session['username']
    cursor = conn.cursor();
    person = "DELETE FROM person WHERE username = %s"
    cursor.execute(person, user)
    photo = "DELETE FROM photo WHERE poster = %s"
    cursor.execute(photo, user)
    fgs = "DELETE FROM friendgroup WHERE groupCreator = %s"
    cursor.execute(fgs, user)
    belongto = "DELETE FROM belongto WHERE username = %s"
    cursor.execute(belongto, user)
    follow = "DELETE FROM follow WHERE follower = %s or followee = %s"
    cursor.execute(follow, (user,user))
    reactto = "DELETE FROM reactto WHERE username = %s"
    cursor.execute(reactto, user)
    sharedwith = "DELETE FROM sharedwith WHERE groupCreator = %s"
    cursor.execute(sharedwith, user)
    tag = "DELETE FROM tag WHERE username = %s"
    cursor.execute(tag, user)
    cursor.close()
    return render_template('index.html')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = False)
