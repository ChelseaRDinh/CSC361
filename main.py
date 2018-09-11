import bottle
import os
import random
import math
import time

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    board_width = data['width']
    board_height = data['height']

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    # TODO: Do things with data

    return {
        'color': '#FF1493',
        'taunt': '{} ({}x{})'.format(game_id, board_width, board_height),
        'head_url': head_url,
        'name': 'Nagini'
    }

#spotsChecked = []
@bottle.post('/move')
def move():
    millis1 = int(round(time.time()*1000))
    snakes = bottle.request.json[u'snakes']
    deadSnakes = bottle.request.json[u'snakes']
    turnNum = bottle.request.json[u'snakes']
    data = bottle.request.json
    foods = bottle.request.json[u'food']
    directions = ['up', 'down', 'right', 'left']
    waysToGo = ['up','down','right','left']
    me = data[u'you']
    meIndex = 0
    boardWidth = data[u'width']-1
    boardHeight = data[u'height']-1
    for i in range(len(snakes)):
        if snakes[i][u'id'] == me:
            meIndex = i

    myLen = len(snakes[meIndex][u'coords'])

    directionDictionary = {'up':[0,-1],'down':[0,1],'right':[1,0], 'left':[-1,0]}
    headx = snakes[meIndex][u'coords'][0][0]
    heady = snakes[meIndex][u'coords'][0][1]

    for wayToGo in directions:
        SpotToCheck = [x+y for x, y in zip([headx, heady], directionDictionary[wayToGo])]
        if occupied_check(SpotToCheck,snakes):
            if wayToGo in waysToGo:
                waysToGo.remove(wayToGo)

    if headx == 0:
        if 'left' in waysToGo:
            waysToGo.remove('left')
    elif headx == boardWidth:
        if 'right' in waysToGo:
            waysToGo.remove('right')
    if heady == boardHeight:
        if 'down' in waysToGo:
            waysToGo.remove('down')
    elif heady == 0:
        if 'up' in waysToGo:
            waysToGo.remove('up')

    # spotsChecked = []
    # waysToGo = decide_direction([headx,heady],snakes, directionDictionary, directions, myLen, boardWidth, boardHeight)
    # print waysToGo
    # if(len(waysToGo) > 0):
    #     maxPotential = 0
    #     bestMove = ''
    #     for wayToGo in waysToGo:
    #         spotToCheck = [x+y for x, y in zip([headx,heady],directionDictionary[wayToGo])]
    #         wayPotential = len(smart_move(spotToCheck,snakes,directionDictionary,directions,[spotToCheck],data))
    #         print wayToGo
    #         print wayPotential
    #         if(wayPotential > maxPotential):
    #             maxPotential = wayPotential
    #             bestMove = wayToGo
    #     waysToGo = [bestMove]

    hunger = 20
    if len(waysToGo) > 0:
        for dirs in food_finder([headx, heady], foods):
            if dirs in waysToGo:
                for i in range(hunger):
                    waysToGo.append(dirs)

    millis2 = int(round(time.time()*1000))
    timeElapsed = millis2-millis1
    if len(waysToGo) > 0:
        return {
            'move': random.choice(waysToGo),
            'taunt': 'Things are getting s-s-s-s-erious!'
        }
    else:
        return {
            'move': 'up',
            'taunt': 'Wow, perfect indentation!!!'
        }

def occupied_check(spot, snakes):
    for snake in snakes:
        if spot in snake[u'coords']:
            return True
    return False

def square(list):
    return map(lambda x: x ** 2, list)

def food_finder(head, foods):
    closest_food = []
    shortestDistance = 1000000
    food_direction = []
    for food in foods:
        distance = math.sqrt(sum(square([x-y for x, y in zip(food, head)])))
        if distance < shortestDistance:
            shortestDistance = distance
            closest_food = food
    if len(closest_food) > 0:
        if([x-y for x, y in zip(closest_food,head)][0] < 0):
            food_direction.append('left')
        elif([x-y for x, y in zip(closest_food, head)][0] > 0):
            food_direction.append('right')
        if([x-y for x, y in zip(closest_food, head)][1] < 0):
            food_direction.append('up')
        elif([x-y for x, y in zip(closest_food, head)][1] > 0):
            food_direction.append('down')
    return food_direction

# def decide_direction(spot,snakes,directionDictionary, directions, myLen, boardWidth, boardHeight):
#     waysToGo = []
#     for direction in directions:
#         spotsChecked = []
#         spotToCheck = [x+y for x, y in zip(spot,directionDictionary[direction])]
#         print spotsChecked
#         print(calc_area(spotToCheck,snakes,directionDictionary,directions,boardWidth,boardHeight))
#         if calc_area(spotToCheck,snakes,directionDictionary,directions,boardWidth,boardHeight) > myLen:
#             waysToGo.append(direction)
#     return waysToGo
#
# def calc_area(spot,snakes,directionDictionary,directions,boardWidth,boardHeight):
#         if occupied_check(spot,snakes) or spot[0] > boardWidth or spot[0] < 0 or spot[1] > boardHeight or spot[1] < 0 or spot in spotsChecked:
#             return 0
#         else:
#             spotsChecked.append(spot)
#             sumz = 0
#             for direction in directions:
#                 spotToCheck = [x+y for x, y in zip(spot,directionDictionary[direction])]
#                 sumz += calc_area(spotToCheck,snakes,directionDictionary,directions,boardWidth,boardHeight)
#             return 1 + sumz




#def smart_move(spot, snakes, directionDictionary, directions, spotList,data):
#    print spotList
#    if occupied_check(spot,snakes):
#        return []
#    for direction in directions:
#        spotToCheck = [x+y for x, y in zip(spot,directionDictionary[direction])]
#        if spotToCheck[0] < 0 or spotToCheck[0] > data[u'width']-1 or spotToCheck[1] < 0 or spotToCheck[1] > data[u'height']-1:
#            return []
        # if spotToCheck not in spotList:
        #     spotList.append(spotToCheck)
        #     return spotList + smart_move(spotToCheck,snakes,directionDictionary,directions,spotList,data)
        # else:
        #     return []


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
