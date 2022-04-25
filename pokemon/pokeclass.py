# pokemon user class

import pokebase as pb
import random
import math
import config
from statclass import PokeStats
from dbclass import db as dbconn


class Pokemon:
    def __init__(self, id_or_name=None):
        self.trainerId = None
        self.discordId = None
        self.id_or_name = id_or_name
        self.name = None
        self.id = None
        self.spriteURL = None
        self.growthRate = None
        self.currentLevel = None
        self.currentExp = None
        self.traded = None
        self.wildPokemon = True
        self.base_exp = None
        self.types = None
        self.hp = PokeStats('hp')
        self.attack = PokeStats('attack')
        self.defense = PokeStats('defense')
        self.speed = PokeStats('speed')
        self.special_attack = PokeStats('special-attack')
        self.special_defense = PokeStats('special-defense')
        self.move_1 = None
        self.move_2 = None
        self.move_3 = None
        self.move_4 = None
        self.currentHP = None
    

    def load(self, trainerId=None):
        """ populates the object with stats from pokeapi """
        if trainerId is None:
            pokemon = pb.pokemon(self.id_or_name)
            self.name = pokemon.species.name
            self.id = pokemon.id
            self.spriteURL = pb.SpriteResource('pokemon', pokemon.id).url
            self.growthRate = pb.pokemon_species(pokemon.id).growth_rate.name
            self.base_exp = pokemon.base_experience
            self.types = self.__getPokemonType()
            moves = self.getMoves()
            self.move_1 = moves[0]
            self.move_2 = moves[1]
            self.move_3 = moves[2]
            self.move_4 = moves[3]
        else:
            # load pokemon from db using trainerId as unique primary key from Pokemon table 
            self.wildPokemon = False
            self.__loadPokemonFromDB(trainerId)
            return

    def create(self, level):
        """ creates a new pokemon with generated stats at a given level """
        # this function is used to create new pokemon and will auto generate their level 1 moves
        self.currentLevel = level
        self.load()
        self.traded = False
        self.currentExp = self.__getBaseLevelExperience()
        self.wildPokemon = True
        ivDict = self.__generatePokemonIV()
        evDict = self.__generatePokemonEV()
        baseDict = self.__getPokemonBaseStats()
        self.__setPokeStats(baseDict, ivDict, evDict)
        moveList = self.getMoves()
        self.move_1 = moveList[0]
        self.move_2 = moveList[1]
        self.move_3 = moveList[2]
        self.move_4 = moveList[3]
        statsDict = self.getPokeStats()
        self.currentHP = statsDict['hp']
    
    def save(self, discordId):
        """ saves a pokemon to the database """
        self.discordId = discordId
        self.__savePokemonToDB()

    def print(self):
        """ prints out all pokemon information for viewing"""
        print('Id:', self.id)
        print('Name:', self.name)
        print('Level:', self.currentLevel)
        print('Exp:', self.currentExp)
        print('Traded:', self.traded)
        print('Types:', self.types)
        print('Stats:', self.getPokeStats())
        print('Moves:', self.getMoves())
    
    def getPokeStats(self):
        """ returns a dictionary of a pokemon's unique stats based off level, EV, and IV """
        statsDict = {}
        level = self.currentLevel

        statsDict['hp'] = self.__calculateUniqueStat(self.hp) + level + 10
        statsDict['attack'] = self.__calculateUniqueStat(self.attack) + 5
        statsDict['defense'] = self.__calculateUniqueStat(self.defense) + 5
        statsDict['speed'] = self.__calculateUniqueStat(self.speed) + 5
        statsDict['special-attack'] = self.__calculateUniqueStat(self.special_attack) + 5
        statsDict['special-defense'] = self.__calculateUniqueStat(self.special_defense) + 5
        return statsDict

    def getMoves(self):
        """ returns a list of the pokemon's current moves """
        moveList = []
        if self.wildPokemon:
            moveDict = self.getPokemonLevelMoves()
            level = self.currentLevel
            # user starter level for pokemon without a level
            if level is None:
                level = config.starterLevel
            # itterate throught he dictionary selecting the top 4 highest moves at the current level
            defaultList = sorted(moveDict.items(), key=lambda x:x[1], reverse=True)
            for move in defaultList:
                moveLevel = move[1]
                moveName = move[0]
                if int(moveLevel) <= level:
                    moveList.append(moveName)
            # check if list is padded to move and if not, append blank moves
            if len(moveList) < 4:
                diff = 4-len(moveList)
                for x in range(diff):
                    x=None
                    moveList.append(x)
        else:
            db = dbconn()
            queryString = "SELECT move_1, move_2, move_3, move_4 FROM pokemon WHERE id = %s"
            results = db.runQuery(queryString, (str(self.trainerId)))
            for result in results:
                moveList = [result[0], result[1], result[2], result[3]]
            # delete object and close connection
            del db
        # return only 4 moves
        return moveList[0: 4]
    
    def getPokemonLevelMoves(self):
        """ returns a dictionary of {move: level} for a pokemons base move set"""
        moveDict = {}
        pokemon = pb.pokemon(self.id)
        for move in pokemon.moves:
            for version in move.version_group_details:
                    if version.version_group.name != config.version_group_name:
                        continue
                    elif version.move_learn_method.name != 'level-up':
                        continue
                    else:
                        moveName = move.move.name
                        moveLevel = version.level_learned_at
                        moveDict[moveName] = moveLevel
        return moveDict

    def evolve(self):
        """ takes a current pokemon and returns an evolved version """
        # todo check if pokemon has evolution, verify level is right
        # retain EV stats through creation. 

        return

    ####
    ###   Private Class Methods
    ####

    def __loadPokemonFromDB(self, trainerId):
        """ loads and creates a pokemon object from the database """
        db = dbconn()
        queryString = 'SELECT id, discord_id, "pokemonId", "pokemonName", "spriteURL", "growthRate", "currentLevel", "currentExp", traded, base_hp, base_attack, base_defense, base_speed, base_special_attack, base_special_defense, "IV_hp", "IV_attack", "IV_defense", "IV_speed", "IV_special_attack", "IV_special_defense", "EV_hp", "EV_attack", "EV_defense", "EV_speed", "EV_special_attack", "EV_special_defense", "move_1", "move_2", "move_3", "move_4", "types", "currentHP" FROM pokemon WHERE id = %s'
        results = db.runQuery(queryString, (str(trainerId)))

        for result in results:
            self.trainerId = result[0]
            self.discordId = result[1]
            self.id_or_name = result[2]
            self.name = result[3]
            self.id = result[2]
            self.spriteURL = result[4]
            self.growthRate = result[5]
            self.currentLevel = result[6]
            self.currentExp = result[7]
            self.traded = result[8]
            self.wildPokemon = False
            self.hp.base = result[9]
            self.attack.base = result[10]
            self.defense.base = result[11]
            self.speed.base = result[12]
            self.special_attack.base = result[13]
            self.special_defense.base = result[14]
            self.hp.IV = result[15]
            self.attack.IV = result[16]
            self.defense.IV = result[17]
            self.speed.IV = result[18]
            self.special_attack.IV = result[19]
            self.special_defense.IV = result[20]
            self.hp.EV = result[21]
            self.attack.EV = result[22]
            self.defense.EV = result[23]
            self.speed.EV = result[24]
            self.special_attack.EV = result[25]
            self.special_defense.EV = result[26]
            self.move_1 = result[27]
            self.move_2 = result[28]
            self.move_3 = result[29]
            self.move_4 = result[30]
            self.types = result[31]
            self.currentHP = result[32]

        # delete and close connectino
        del db
        return 

    def __savePokemonToDB(self):
        """ saves pokemon using trainerId to database """
        # this function assumes the pokemon class object is already populated
        db = dbconn()
        
        if self.trainerId is None:
            queryString = 'INSERT INTO pokemon(discord_id, "pokemonId", "pokemonName", "spriteURL", "growthRate", "currentLevel", "currentExp", traded, base_hp, base_attack, base_defense, base_speed, base_special_attack, base_special_defense, "IV_hp", "IV_attack", "IV_defense", "IV_speed", "IV_special_attack", "IV_special_defense", "EV_hp", "EV_attack", "EV_defense", "EV_speed", "EV_special_attack", "EV_special_defense", move_1, move_2, move_3, move_4, types) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        else:
            queryString = """
                UPDATE pokemon
                    SET discord_id=%s, "pokemonId"=%s, "pokemonName"=%s, "spriteURL"=%s, "growthRate"=%s, "currentLevel"=%s, "currentExp"=%s, traded=%s, base_hp=%s, base_attack=%s, base_defense=%s, base_speed=%s, base_special_attack=%s, base_special_defense=%s, "IV_hp"=%s, "IV_attack"=%s, "IV_defense"=%s, "IV_speed"=%s, "IV_special_attack"=%s, "IV_special_defense"=%s, "EV_hp"=%s, "EV_attack"=%s, "EV_defense"=%s, "EV_speed"=%s, "EV_special_attack"=%s, "EV_special_defense"=%s, move_1=%s, move_2=%s, move_3=%s, move_4=%s, types=%s
                    WHERE id = %s;
            """
        values = (self.discordId, self.id, self.name, self.spriteURL, self.growthRate, self.currentLevel, self.currentExp, self.traded, self.hp.base, self.attack.base, self.defense.base, self.speed.base, self.special_attack.base, self.special_defense.base, self.hp.IV, self.attack.IV, self.defense.IV, self.speed.IV, self.special_attack.IV, self.special_defense.IV, self.hp.EV, self.attack.EV, self.defense.EV, self.speed.EV, self.special_attack.EV, self.special_defense.EV, self.move_1, self.move_2, self.move_3, self.move_4, self.types)
        
        if self.trainerId is not None:
            values = values + (self.trainerId,)
        
        db.runUpdateQuery(queryString, values)

        # delete and close connectino
        del db
        return 
    def __getPokemonType(self):
        """ returns string of pokemons base type """
        typeList = []
        pokemon = pb.pokemon(self.id)
        for type in pokemon.types:
            typeList.append(type.type.name)
        
        return typeList

    def __getNewMoves(self):
        """ returns a pokemons moves at a specific level """
        newMoves = {}
        moveDict = self.getPokemonLevelMoves()
        for key, value in moveDict.items():
            if value == self.currentLevel:
                newMoves[key] = value
        return newMoves

    def __calculateUniqueStat(self, statObj):
        """ returns integer of a stat calculated from various parameters """
        level = self.currentLevel
        EV = statObj.EV
        IV = statObj.IV
        base = statObj.base
        evCalc = math.floor(math.ceil(math.sqrt(EV))/4)
        baseIVCalc = (base + IV) * 2
        numerator = (baseIVCalc + evCalc) * level
        baseCalc = math.floor(numerator/100)
        return baseCalc

    def __generatePokemonIV(self):
        """ returns dictionary of random generated individual values """
        # a pokemon has 6 IVs for each base stat
        # attack, defense, speed, special_attack, and special_defense are random 0-15
        # hp is calculated from the other IV using a binary string conversion formula
        ivDict = {}
        attack = random.randrange(0,16)
        defense = random.randrange(0,16)
        speed = random.randrange(0,16)
        special_attack = random.randrange(0,16)
        special_defense = special_attack

        hp = int(format(attack, 'b').zfill(4)[3] + format(defense, 'b').zfill(4)[3] + format(speed, 'b').zfill(4)[3] + format(special_attack, 'b').zfill(4)[3], 2)

        ivDict['hp'] = hp
        ivDict['attack'] = attack
        ivDict['defense'] = defense
        ivDict['speed'] = speed
        ivDict['special-attack'] = special_attack
        ivDict['special-defense'] = special_defense
        return ivDict

    def __generatePokemonEV(self):
        """ returns dictionary of base generated effort values """
        evDict = {'hp': 1, 'attack': 1, 'defense': 1, 'speed': 1, 'special-attack': 1, 'special-defense': 1}
        return evDict

    def __getPokemonBaseStats(self):
        """ returns dictionary of {stat: value} for a pokemons base stats """
        baseDict = {}
        pokemon = pb.pokemon(self.id)
        for stat in pokemon.stats:
            statName = stat.stat.name
            statVal = stat.base_stat
            baseDict[statName] = statVal
        return baseDict

    def __getBaseLevelExperience(self):
        """ returns minimum total experience at a given level """
        if self.growthRate == 'Fast':
            return round(0.8 * (self.currentLevel ** 3))
        elif self.growthRate == 'medium-fast':
            return round(self.currentLevel ** 3)
        elif self.growthRate == 'medium-slow':
            return round(1.2*(self.currentLevel ** 3)-(15*(self.currentLevel ** 2)) + 100*self.currentLevel - 140)
        elif self.growthRate == 'slow':
            return round(1.25 * (self.currentLevel ** 3))
        else:
            return None

    def __setPokeStats(self, baseDict, ivDict, evDict):
        """ populates PokeStats class value with given stats """
        self.hp.base = baseDict['hp']
        self.hp.IV = ivDict['hp']
        self.hp.EV = evDict['hp']

        self.attack.base = baseDict['attack']
        self.attack.IV = ivDict['attack']
        self.attack.EV = evDict['attack']

        self.defense.base = baseDict['defense']
        self.defense.IV = ivDict['defense']
        self.defense.EV = evDict['defense']

        self.speed.base = baseDict['speed']
        self.speed.IV = ivDict['speed']
        self.speed.EV = evDict['speed']

        self.special_attack.base = baseDict['special-attack']
        self.special_attack.IV = ivDict['special-attack']
        self.special_attack.EV = evDict['special-attack']

        self.special_defense.base = baseDict['special-defense']
        self.special_defense.IV = ivDict['special-defense']
        self.special_defense.EV = evDict['special-defense']




# pokemon = Pokemon()

# pokemon.load(trainerId=2)

# pokemon.create(8)
# pokemon.save('123')



# pokemon.print()
# print(pokemon.getPokeStats())


# pokemon = pb.pokemon(150)
# location = pokemon.location_area_encounters
# for loc in location:
#     print(loc.location_area.url)



# print(pokemonEncounterList)


    # print(encounter.pokemon.name)
# print(locObj.pokemon_encounters)
# print(location[0].location_area)
# print(dir(location[0].version_details))

# print(area)



