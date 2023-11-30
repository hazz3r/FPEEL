import copy,json

# I made some proof of concept code, doesnt do the full algorimth but it proves that this works well
# I didnt have data to deal with positions, so that doesnt exist, should be easy to add
# Currently the thing has no problem with stuf having to be binary on/off, its just spits out the right values


def simplex(tableau):
    print('Iteration')
    tableau = copy.deepcopy(tableau)
    vals = tableau.pop(0)
    pivot_column = tableau[-1].index(min(tableau[-1]))
    
    # Check if algorithm is finished
    if tableau[-1][pivot_column]<0:
        
        # Main simplex method code
        theta = []
        for r in range(len(tableau)-1):
            if tableau[r][pivot_column] == 0 or tableau[r][-1]/tableau[r][pivot_column]<0:
                theta.append(float('inf'))
            else: theta.append(tableau[r][-1]/tableau[r][pivot_column])
        pivot_row = theta.index(min(theta))
        rowoper = []
        for y in range(len(tableau)):
            if y != pivot_row:
                rowoper.append((tableau[y],-tableau[y][pivot_column]/tableau[pivot_row][pivot_column],tableau[pivot_row]))
            else:
                rowoper.append(([0 for a in range(len(tableau[y]))],1/tableau[y][pivot_column],tableau[y]))
        ntable = []
        for r in rowoper:
            ntable.append([r[0][i]+r[1]*r[2][i] for i in range(len(r[0]))])

        return simplex([vals]+ntable)        

    ## Some processing garbage to extract the data from the tableau
    output = {}
    for col in range(len(tableau[0])-1):
        one = -1
        for y in range(len(tableau)):
            if tableau[y][col] in [0,1]:
                if tableau[y][col] == 1 and one!=-1:
                    output[vals[col]] = 0
                    break
                elif tableau[y][col] == 1:
                    one = y
            else:
                output[vals[col]] = 0
                break
        if not vals[col] in output:
            output[vals[col]] = tableau[one][-1]


    ## Shove crap into some strings
    st = ''
    st2 = ''
    stimportant = ''
    for a in output:
        if str(output[a])[-2:] == '.0': output[a] = int(output[a])
        if output[a]!=0:
            st+=f'{a}={round(output[a],3)}, '
            if 'p' in a:
                stimportant+=f'{a}={round(output[a],3)}, '
        else: st2+=f'{a}={round(output[a],3)}, '
    st2.removesuffix(', ')
    
    print('Players =',stimportant)
    print('Total Value =',round(tableau[-1][-1],3))
    
##    print('Values = '+st+'\nZeros = '+st2+f'\nProfit = {round(tableau[-1][-1],3)}')

    return tableau 

def playertableau(budget):
    with open('dummydata.json','r') as f:
        players = json.load(f)
    table = []
    # Main equations
    table.append([a['cost'] for a in players]+[budget])
    for a in range(len(players)):
        table.append([0 for b in range(len(players))]+[1])
        table[-1][a] = 1
    
    # Add slack
    slacknum = len(table)
    for b in range(len(table)):
        for s in range(slacknum):
            if s!=b: table[b].insert(-1,0)
            else: table[b].insert(-1,1)
            
    # Player limit to 15
    table.append([1 for a in range(len(players))]+[0 for a in range(slacknum)]+[15])

    ## I dont have the data for player positions but that is easy to add
    
    # Max function
    table.append([-a['composite'] for a in players]+[0])
    while len(table[-1])<len(table[0]):
        table[-1].insert(-1,0)
    table.insert(0,['p'+str(b) for b in range(len(players))]+['s'+str(a) for a in range(slacknum)]+['Values'])

    return table


tableau = playertableau(500)
simplex(tableau)
