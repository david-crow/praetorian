# https://www.praetorian.com/challenges/mastermind/
# hash: 0db0da84d42a2854809732817ae1c052df31e385a6fff5c71df1eef727efe0777b2275736572223a202264617669647268656163726f7740676d61696c2e636f6d227d

import requests
import json
import itertools
import random

# initialize stuff for Praetorian's API
email, root = "davidrheacrow@gmail.com", "https://mastermind.praetorian.com"
headers = requests.post(f"{root}/api-auth-token/", data={"email": email}).json()
headers["Content-Type"] = "application/json"
requests.post(f"{root}/reset/", headers=headers)

# retrieve the next level of the game
def getLevel(level):
    url = f"{root}/level/{level}/"
    return url, requests.get(url, headers=headers)

# submit a guess for the current level
def sendGuess(url, data):
    return requests.post(url, data=json.dumps({"guess": data}), headers=headers)

# identify 12 or fewer weapons for the current level
# specifically, when the number of weapons is large, the number of permutations is massive
# so we filter out weapons prior to generating the permutations
def identifyWeapons(url, level):
    weapons = list(range(level["numWeapons"]))
    guess, key = None, None

    # generate all combinations of the weapons -- order does not matter
    combs = list(itertools.combinations(weapons, level["numGladiators"]))

    while len(set(itertools.chain(*combs))) > 12:
        guess = random.choice(combs)
        level["numGuesses"] -= 1
        key = sendGuess(url, guess).json()["response"]

        # filter out all weapons combinations that don't have exactly `key[0]` of the weapons in the current guess
        # here, `key[0]` is the number of weapons used against the correct gladiator
        combs = list(filter(lambda comb : sum(n in guess for n in comb) == key[0], combs))

    # flatten the combinations to obtain a new list of weapons
    return set(itertools.chain(*combs))

# filter out all weapons permutations that don't fit the feedback returned after a guess
def filterPerms(guess, perms, key):
    def keepPerm(perm):
        return (sum(n in guess for n in perm) == key[0]
            and sum(x == y for x, y in zip(perm, guess)) == key[1])

    perms = list(filter(keepPerm, perms))
    return perms

# pick a permutation to submit for the next guess
def makeGuess(guess, perms, key):

    # if we don't yet have any feedback, just submit a list of the first `numGladiators` weapons
    if key is None:
        return perms, list(range(len(perms[0])))

    # otherwise, filter the permutations according to the previous guess's feedback
    perms = filterPerms(guess, perms, key)

    # we could order the permutations by potential filtering for the next guess, but it's unnecessary here
    # for harder (e.g., more constrained) problems, we'd have to order the permutations to speed execution
    return perms, perms.pop(0)

# the driver function for the current level
def solve(level_num, data):
    url, level = data[0], data[1].json()
    print(f"\n{level_num}: {level}\n")

    for i in range(level["numRounds"]):
        print(f"\tRound {i + 1}")

        # initalize the guess and feedback;
        # identify 12 or fewer weapons; and
        # generate all permutations of `numGladiators` weapons
        guess, key = None, None
        weapons = identifyWeapons(url, level)
        perms = list(itertools.permutations(weapons, level["numGladiators"]))

        for _ in range(level["numGuesses"]):
            perms, guess = makeGuess(guess, perms, key)
            response = sendGuess(url, guess).json()

            # if we've solved either the level or the entire game
            if "message" in response:
                if response["message"] == "Congratulations!":
                    return False, response["hash"]

                return True, None

            # if we've solved the current round and there are more rounds
            elif "roundsLeft" in response:
                break

            # dang, ran out of guesses
            elif "error" in response:
                print(f"\t{response['error']}")
                return False, None

            # otherwise, update the feedback and make another guess
            key = response["response"]

# driver function
def main():
    play = True
    level_num = 1

    # while there are still levels to solve
    while play:
        play, hash = solve(level_num, getLevel(level_num))
        level_num += 1

    print(f"\nHash: {hash}")

if __name__ == "__main__":
    main()
