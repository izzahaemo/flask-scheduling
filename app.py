
from flask import Flask, flash, render_template, json, request, redirect, url_for, session, send_from_directory
import random
import random as rd
import numpy as np
import sys
import mysql.connector
import pandas as pd
import sqlalchemy

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'eventmanagement'


@app.route('/')
def main():
    return '<h1>Belajar Web dengan Python</h1>'


@app.route('/buat/<path:ide>')
def buat(ide):

    ################################################################################

    # Koneksi database

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="eventmanagement"
    )
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM data_mhs WHERE ide=%s", (ide,))
    user = cursor.fetchall()

    # menghitung total data mhs

    total_user = 0
    for data in user:
        total_user = total_user + 1

    # menjadikan data mhs ke numpy

    user_data = np.array(user)

    # menghitung banyaknya jadwal

    cursor.execute(
        "SELECT * FROM schedule_on WHERE ide=%s", (ide,))
    schedule = cursor.fetchall()

    total_schedule = 0
    for data in schedule:
        total_schedule = total_schedule + 1

    schedule_data = np.array(schedule)

    ################################################################################

    # inisialisasi

    t = 1
    w = 0.7           # inertia
    c1 = 1.8          # cognitive (particle)
    c2 = 1.3          # social (swarm)

    c = 9

    iterations = 500                # particle move
    dimensions = 7                  # dimensions / total divisi
    all_particle = total_schedule   # particle in the swarm / total schedule
    min_value = 1                   # minimum value

    # menghitung maximum value tiap partikel

    max_value = np.zeros((dimensions + 1, 1)).astype("int")
    max_all = 0

    for i in range(total_user):
        for x in range(dimensions):
            if user[i][1] == x+1:
                max_value[x+1] = max_value[x+1] + 1
                user_data[i][4] = max_value[x+1][0]
                if max_all < max_value[x+1][0]:
                    max_all = max_value[x+1][0]

    max_value_all = [max_value[i+1][0]+1 for i in range(dimensions)]

    # init particle position value

    particle_position = np.random.randint(
        1, [max_value_all for x in range(all_particle)]).astype("float")

    # init particle velocity value

    particle_velocity = np.random.randint(
        1, [max_value_all for x in range(all_particle)]).astype("float")

    # particle fitness

    particle_fitness = np.zeros((all_particle, 1))

    # particle best fitness first value

    best_particle_fitness = np.zeros((all_particle, 1))

    # particle best positions first value

    best_particle_position = np.zeros((all_particle, dimensions))

    # np array untuk menghitung penggunaan satu orang per divisi

    total_use = np.zeros((dimensions, max_all + 1))
    check_use = np.zeros((dimensions))
    max_use = np.zeros((dimensions, 1)).astype("int")
    is_fix = np.zeros((all_particle, 1))
    for i in range(dimensions):
        max_use[i] = 20/max_value[i+1] + 1

    for i in range(all_particle):
        print("first in ", i+1, " = ", particle_position[i])

    ################################################################################

    # update Fitness

    def update_fitness(position):
        error = 0
        for i in range(dimensions):
            check_use[i] = total_use[i][particle_position[position]
                                        [i].astype("int")].astype("int") + 1

            if check_use[i] > max_use[i]:
                error = error + 1
            elif check_use[i] == max_use[i]:
                for x in range(max_value[i+1][0]):
                    if total_use[i][x+1] == 0:
                        error = error + 1
                        x = max_value[i+1][0]
            for x in range(total_user):
                if user_data[x][1].astype("int") == i + 1 and particle_position[position][i] == user_data[x][4].astype("int"):
                    if user_data[x][3][position+1] == '0':
                        error = error + 1
        return error

    def update_fitness2(position):
        error = 0
        for i in range(dimensions):
            check_use[i] = total_use[i][best_particle_position[position]
                                        [i].astype("int")].astype("int") + 1

            if check_use[i] > max_use[i]:
                error = error + 1
            elif check_use[i] == max_use[i]:
                for x in range(max_value[i+1][0]):
                    if total_use[i][x+1] == 0:
                        error = error + 1
                        x = max_value[i+1][0]
            for x in range(total_user):
                if user_data[x][1].astype("int") == i + 1 and best_particle_position[position][i] == user_data[x][4].astype("int"):
                    if user_data[x][3][position+1] == '0':
                        error = error + 1
        return error

    ################################################################################

    # update velocity

    def update_velocity(i, y):

        # generate random numbers
        r1 = random.random()
        r2 = random.random()

        # the learning rate part
        part_1 = (w * particle_velocity[i][y])
        # the cognitive part - learning from itself
        part_2 = (
            c1 * r1 * (best_particle_position[i][y] - particle_position[i][y]))
        # the social part - learning from others
        part_3 = (
            c2 * r2 * (best_swarm_positions[y] - particle_position[i][y]))

        new_velocity = part_1 + part_2 + part_3

        return new_velocity

    ################################################################################

    # update Fitness

    def update_use(position):

        for i in range(dimensions):
            total_use[i][best_particle_position[position][i].astype(
                "int")] = total_use[i][best_particle_position[position][i].astype("int")] + 1
            if total_use[i][best_particle_position[position][i].astype(
                    "int")] == max_use[i]:
                total_use[i][0] = total_use[i][0] + 1

        return 1

    ################################################################################

    # proses repair

    def updatelast(y, i):
        counter = np.zeros(max_value[i+1][0])
        new = 0
        g = 0
        z = random.randint(0, max_value[i+1][0] - 1)
        while(g < max_value[i+1][0]):

            if counter[z] == 0:
                counter[z] = 1
                g = g + 1

            check_use[i] = total_use[i][z + 1] + 1

            if check_use[i] < max_use[i] + 1:
                for x in range(total_user):
                    if user_data[x][1].astype("int") == i + 1 and z + 1 == user_data[x][4].astype("int"):
                        if user_data[x][3][y+1] == '1':
                            new = z + 1
                            g = max_value[i+1][0]

            z = random.randint(0, max_value[i+1][0] - 1)

            if g == max_value[i+1][0]:

                for a in range(max_value[i+1][0]):
                    check_use[i] = total_use[i][a + 1] + 1

                    if check_use[i] == 1:

                        for x in range(total_user):

                            if user_data[x][1].astype("int") == i + 1 and a + 1 == user_data[x][4].astype("int"):
                                if user_data[x][3][y+1] == '1':
                                    new = a + 1
                                    g = max_value[i+1][0]

        return new

    ################################################################################

    qwe = 0
    # find best fitnes and positions first

    best_swarm_fitness = 10
    best_swarm_positions = np.zeros((dimensions, 1))

    # update first time particle fitness, best fitness, and best positions

    for i in range(all_particle):
        particle_fitness[i] = update_fitness(i)
        best_particle_fitness[i] = particle_fitness[i]
        best_particle_position[i] = particle_position[i]

        if particle_fitness[i] == 0:
            is_fix[i] = update_use(i)
            qwe = qwe + 1
            print("Particel ", i, "dapat ",
                  best_particle_fitness[i], "ke 0", " ", qwe, " ", best_swarm_positions)

        if best_swarm_fitness > particle_fitness[i].astype("int"):
            best_swarm_fitness = particle_fitness[i].astype("int")
            best_swarm_positions = list(particle_position[i])

    ################################################################################

    # PSO

    for __x in range(iterations):
        for i in range(all_particle):

            # Update Velocity
            for y in range(dimensions):
                particle_velocity[i][y] = update_velocity(i, y)

            # Update Positions
            for y in range(dimensions):

                particle_position[i][y] = particle_position[i][y] + \
                    particle_velocity[i][y]
                if particle_position[i][y] < min_value:
                    particle_position[i][y] = min_value
                elif particle_position[i][y] > max_value[y+1]:
                    particle_position[i][y] = max_value[y+1]
                # pembulatan
                particle_position[i][y] = round(particle_position[i][y])

            # Update Used

            if best_particle_fitness[i] == 0 and is_fix[i] == 0:
                is_fix[i] = update_use(i)
                qwe = qwe + 1
                print("Particel ", i + 1, "dapat ",
                      best_particle_fitness[i], "ke ", __x + 1, " ", qwe, " ", best_swarm_positions)

            # Proses Repair

            if best_particle_fitness[i] != 0:
                for y in range(dimensions):
                    check_use[y] = total_use[y][particle_position[i]
                                                [y].astype("int")].astype("int") + 1

                    if check_use[y] > max_use[y]:
                        particle_position[i][y] = updatelast(i, y)

                    elif check_use[y] == max_use[y]:
                        for x in range(max_value[y+1][0]):
                            if total_use[y][x+1] == 0:
                                particle_position[i][y] = updatelast(i, y)
                                x = max_value[y+1][0]

                    for x in range(total_user):
                        if user_data[x][1].astype("int") == i + 1 and particle_position[i][y] == user_data[x][4].astype("int"):
                            if user_data[x][3][i+1] == '0':
                                particle_position[i][y] = updatelast(i, y)

            # Update Fitness

            particle_fitness[i] = update_fitness(i)

            # are the new positions a new best for the particle?

            if best_particle_fitness[i].astype("int") > particle_fitness[i].astype("int"):
                best_particle_fitness[i] = particle_fitness[i].astype("int")
                best_particle_position[i] = list(particle_position[i])
            elif best_particle_fitness[i] != 0:
                best_particle_fitness[i] = update_fitness2(i)

            # Update Used

            if best_particle_fitness[i] == 0 and is_fix[i] == 0:
                is_fix[i] = update_use(i)
                qwe = qwe + 1
                print("Particel ", i + 1, "dapat ",
                      best_particle_fitness[i], "ke ", __x + 1, " ", qwe, " ", best_swarm_positions)

            # are the new positions a new best overall?

            if best_swarm_fitness > particle_fitness[i].astype("int") or particle_fitness[i].astype("int") == 0:
                best_swarm_fitness = particle_fitness[i].astype("int")
                best_swarm_positions = list(particle_position[i])

        if __x == 100:
            print("Iterasi ", __x)
        elif __x == 200:
            print("Iterasi ", __x)
        elif __x == 300:
            print("Iterasi ", __x)
        elif __x == 400:
            print("Iterasi ", __x)
        elif __x == 500:
            print("Iterasi ", __x)

        ab = 0
        for i in range(all_particle):
            if best_particle_fitness[i] == 0:
                ab = ab + 1
        if ab == all_particle:
            break

    ################################################################################

    # lihat data

    for i in range(all_particle):
        print("fitnsess in ", i+1, " = ", best_particle_fitness[i])

    for i in range(all_particle):
        print("best in ", i+1, " = ", best_particle_position[i])

    print(best_swarm_positions)

    print("Yang Berfitness 0")
    zero = 0
    for i in range(all_particle):
        if best_particle_fitness[i] == 0:
            zero = zero + 1
            print("Partikel ke", i+1, " = ", best_particle_position[i])

    print("Sebanyak ", zero)
    print(total_use)

    ################################################################################

    # check data error

    g = 0

    # check Data

    for y in range(all_particle):
        if best_particle_fitness[y] != 0:
            for i in range(dimensions):
                check_use[i] = total_use[i][best_particle_position[y]
                                            [i].astype("int")].astype("int") + 1
                if check_use[i] > max_use[i]:
                    g = g + 1
                    print("Partikel ", y+1, " Error di used ", i+1, " ", best_particle_position[y]
                          [i])
                elif check_use[i] == max_use[i] and total_use[i][0] == 10:
                    g = g + 1
                    print("Partikel ", y+1, " Error di usedv ", i+1, " ", best_particle_position[y]
                          [i])
                for x in range(total_user):
                    if user_data[x][1].astype("int") == i + 1 and best_particle_position[y][i] == user_data[x][4].astype("int"):
                        if user_data[x][3][y+1] == '0':
                            g = g + 1
                            print("Partikel ", y+1, " Error di jadwal ", i+1, " ", best_particle_position[y]
                                  [i])
    print(g)

    ################################################################################

    # ubah dimensi yang masih error

    for y in range(all_particle):
        if best_particle_fitness[y] != 0:
            for i in range(dimensions):
                check_use[i] = total_use[i][best_particle_position[y]
                                            [i].astype("int")].astype("int") + 1
                if check_use[i] > max_use[i]:
                    best_particle_position[y][i] = 0
                elif check_use[i] == max_use[i] and total_use[i][0] == 10:
                    best_particle_position[y][i] = 0
                for x in range(total_user):
                    if user_data[x][1].astype("int") == i + 1 and best_particle_position[y][i] == user_data[x][4].astype("int"):
                        if user_data[x][3][y+1] == '0':
                            best_particle_position[y][i] = 0

                if best_particle_position[y][i] != 0:
                    total_use[i][best_particle_position[y][i].astype(
                        "int")] = total_use[i][best_particle_position[y][i].astype("int")] + 1
                    if total_use[i][best_particle_position[y][i].astype(
                            "int")] == max_use[i]:
                        total_use[i][0] = total_use[i][0] + 1

    print("Total use baru")
    print(total_use)

    ################################################################################

    # Proses memasukkan ke database

    particle_results = np.zeros((all_particle, dimensions + 2))

    for y in range(all_particle):
        particle_results[y][0] = schedule_data[y][0]
        particle_results[y][1] = 0
        for i in range(dimensions):
            for x in range(total_user):
                if user_data[x][1].astype("int") == i + 1 and best_particle_position[y][i] == user_data[x][4].astype("int"):
                    particle_results[y][i+2] = user_data[x][0].astype("int")
            if particle_results[y][i+2] == 0:
                particle_results[y][1] = particle_results[y][1] + 1

    print(particle_results)

    engine = sqlalchemy.create_engine(
        "mariadb+pymysql://root:@localhost/eventmanagement")
    particle_results1 = pd.DataFrame(particle_results, columns=[
        'id_schedule', 'is_fine', 'div_1', 'div_2', 'div_3', 'div_4', 'div_5', 'div_6', 'div_7'])
    print(particle_results1)

    sqll = "TRUNCATE TABLE schedule_tempory"
    cursor.execute(sqll)
    db.commit()

    particle_results1.to_sql(
        name='schedule_tempory',
        con=engine,
        index=False,
        if_exists='append'
    )

    ################################################################################

    return redirect("http://localhost/eventmanagementci3/schedule/goto/" + str(ide))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002)
