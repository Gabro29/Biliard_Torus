# This program is a simulation of a bouncing ball in a base x height rectangle made in matplotlib.
# The path of the ball is a straight line, when it hits a side of the square it will
# bounce by following the rule that the new line is build by mirroring the previous one.
# This is done thanks to math by using the slope of the line and by taking the opposite
# of this value. Note that the angle cannot be equals to 90°, because in that case
# there will be a loop. But there is also a math proof for that, because tg(90) does not
# exist, infact slope = tg(angle_x_axis).

# Update:
# Now I made a 3D plot to visualize the path of the ball. In fact if we glue the upper and the bottom side
# together and the left and the right side we obtain a Torus. It has been difficult since I'm not an expert.
# after a day of full reflection in my swimming pool, I figured out how to convert plane coordinates into a 3D line
# which follows the surface of the Torus.

# Furthermore SPAWN POINT and SLOPE can be random values. But I found some special values to demonstrate that
# if the path of the ball is not periodically then the entire surface of the Torus is covered. Otherwise, there will be
# a few lines and the Torus will be somehow 'naked'.



# LAST UPDATE
# alpha, beta,



import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
import pandas as pd
from mpl_toolkits.mplot3d.art3d import Path3DCollection, Line3DCollection
import numpy as np
import sympy
from math import sqrt, hypot, fsum, atan, cos
from threading import Thread
from time import time


sympy.init_printing()


def initialize_csv():
    with open("vals_to_study.csv", "w") as file:
        file.write("Punto_Intersezione,Somma_Segmenti,Passo_Teta,Min_Dist,Beta,Alfa,Slope,Tempo\n")


def get_collision_with_line_oneD(initial_point: float, slope: float, intercept: float):
    """Get intersection with red line"""

    global SPAWN_POINT, base_rect

    # Matrix's coefficents of trajectory and red line
    M = sympy.Matrix([[-slope, 1], [0, 1]])

    # Build the terms know matrice
    b = sympy.Matrix([intercept, SPAWN_POINT[1]])

    solution = M.solve(b)
    if solution[1] == SPAWN_POINT[1] and 0 <= solution[0] <= base_rect:
        return solution
    else:
        return None


def length_segmnet(x1: float, x2: float, y1: float, y2: float):
    """Compute Pitagora's Theorem to calculate the length of the line"""

    return hypot(fsum([x2, -x1]), fsum([y2, -y1]))


def get_teta(m: float, sum_of_segments: list):
    """Calculate step of onedimensional case"""
    return cos(atan(m)) * fsum(sum_of_segments)


def get_beta(m: float, sum_of_segments: list):
    """Returns velocity on y"""
    return 1 / (get_teta(m=slope, sum_of_segments=sum_of_segments))


def get_alpha(m: float, sum_of_segments: list):
    """Returns velocity on x"""
    return 1 / (cos((np.pi / 2) - atan(m)) * fsum(sum_of_segments))


def write_onf_file(red_count: int, red_intersection, sum_of_segments: list, min_dist, tempo):

    global slope, df_vals

    df_temp = pd.DataFrame(columns=["Punto_Intersezione", "Somma_Segmenti", "Passo_Teta", "Min_Dist", "Beta", "Alfa", "Slope", "Tempo"])
    df_temp["Punto_Intersezione"] = pd.Series(f"[{red_intersection[0]}, {red_intersection[1]}]")
    df_temp["Somma_Segmenti"] = pd.Series(fsum(sum_of_segments))
    df_temp["Passo_Teta"] = pd.Series(get_teta(m=slope, sum_of_segments=sum_of_segments))
    df_temp["Min_Dist"] = pd.Series(min_dist)
    df_temp["Beta"] = pd.Series(get_beta(slope, sum_of_segments))
    df_temp["Alfa"] = pd.Series(get_alpha(slope, sum_of_segments))
    df_temp["Slope"] = pd.Series(slope)
    df_temp["Tempo"] = pd.Series(tempo)

    df_vals = pd.concat([df_vals, df_temp])

    df_vals.to_csv("vals_to_study.csv", index=False)


def abs_min_distance(red_intersection, previous_intersection):
    """Returns distance based on the rule min |x-y|, |x-y-1|,|x-y+1|"""

    return min([abs(red_intersection[0] - previous_intersection[0]), abs(red_intersection[0] - previous_intersection[0] + 1),
                   abs(red_intersection[0] - previous_intersection[0] - 1)])


def collision_check(slope: float, intercept: float, initial_point: list):
    """Gives the intersection point with the rectangle edges and the side hitten"""

    global base_rect, height_rect

    # Let's build a matrix where first row is
    # the line's expression and second row is
    # one of the four rectangle's edges.

    # Create a list of matrices, so we have to solve
    # four systems.
    MMs = [sympy.Matrix([[-slope, 1], [1, 0]]),  # Left Side
           sympy.Matrix([[-slope, 1], [0, 1]]),  # Bottom Side
           sympy.Matrix([[-slope, 1], [1, 0]]),  # Right Side
           sympy.Matrix([[-slope, 1], [0, 1]]),  # Up Side
           ]
    # Build the terms know matrices to pair with previous list MMs
    bbs = [sympy.Matrix([intercept, 0]),  # Left side
           sympy.Matrix([intercept, 0]),  # Bottom side
           sympy.Matrix([intercept, base_rect]),  # Right Side, change also rectangle dim
           sympy.Matrix([intercept, height_rect]),  # Up Side, change also rectangle dim
           ]
    # Build a dictionary to correlate each b to the corresponding side
    sides_dict = {0: "Left Side", 1: "Bottom Side", 2: "Right Side", 3: "Up Side"}
    # Solve each system and get only the wnated solution
    for index, (M, b) in enumerate(zip(MMs, bbs)):
        solution = M.solve(b)
        if 0 <= solution[0] <= base_rect and 0 <= solution[1] <= height_rect and solution[0] != initial_point[0] \
                and solution[1] != initial_point[1]:
            return [solution[0], solution[1]], sides_dict[index]
        elif solution[0] == 0 and solution[1] == 0:
            print(f"Hitted the Bottom-Left Corner")
            # exit()
        elif solution[0] == 0 and solution[1] == height_rect:
            print(f"Hitted the Upper-Left Corner")
            # exit()
        elif solution[0] == base_rect and solution[1] == 0:
            print(f"Hitted the Bottom-RightCorner")
            # exit()
        elif solution[0] == base_rect and solution[1] == height_rect:
            print(f"Hitted the upper-Right Corner")
            # exit()


def mirror_line(slope: float, intercept: float, start_point: list):
    """Gives parameters for the new mirrored line"""
    # Revert the slope
    slope = -slope
    # Find the intercept
    intercept = start_point[1] - slope * start_point[0]
    return slope, intercept


def animate(i, base_rect: int, height_rect: int, r: int):
    """Draws the path of the ball, both in the 2D and 3D graphs"""

    global slope, intercept, starting_point, dir_name, index, sum_of_segments, red_count, SPAWN_POINT, \
        previous_intersection, T_i

    if T_i is None:
        T_i = time()


    # Get intersection with edge and side hitten
    try:
        new_point, side_hitten = collision_check(slope, intercept, initial_point=starting_point)
    except TypeError:
        print("Corner Hitten. I'm in a loop...")
        input("Press ENTER to stop...")
        exit(1)


    # Draw 2D line
    if starting_point[0] < new_point[0]:
        x1 = starting_point[0]
        x2 = new_point[0]
        y1 = intercept + slope * x1
        y2 = intercept + slope * x2
        x_vals = np.arange(starting_point[0] - 0.001, new_point[0], 0.001)
    else:
        x1 = new_point[0]
        x2 = starting_point[0]
        y1 = intercept + slope * x1
        y2 = intercept + slope * x2
        x_vals = np.arange(new_point[0] - 0.001, starting_point[0], 0.001)

    y_vals = intercept + slope * x_vals
    # Plot line in 2D
    ax_2d.plot(x_vals, y_vals, color="cyan")

    # Back to 1D
    # Calculate intersection with red line
    red_intersection = get_collision_with_line_oneD(starting_point, slope, intercept)

    if red_intersection is not None and red_intersection[0] != SPAWN_POINT[0]:
        # Split line if red line is hitted
        sum_of_segments.append(length_segmnet(x1=red_intersection[0], x2=x2,
                                              y1=red_intersection[1], y2=y2))
        # print(f"Becco la linea e i segmenti sono {sum_of_segments}")
        # Write on file values
        T_f = time()
        min_dist = abs_min_distance(red_intersection, previous_intersection)
        Thread(target=write_onf_file(red_count, red_intersection, sum_of_segments, min_dist, T_f - T_i)).start()
        T_i = None

        # Initialize a new path
        sum_of_segments.clear()
        # print("PULISCO")
        sum_of_segments.append(length_segmnet(x2=red_intersection[0], x1=x1,
                                              y2=red_intersection[1], y1=y1))
        # print(f"Il segmento dopo la linea {sum_of_segments}")

        # Increase number of points in the red line
        red_count += 1
        previous_intersection = red_intersection

    else: # If no red line is hitted
        sum_of_segments.append(length_segmnet(x2=x2, x1=x1, y2=y2, y1=y1))
        # print(f"Nessuna linea colpita {sum_of_segments}")


    # 3D plot with Torus
    teta = 2 * np.pi * x_vals / base_rect
    fi = 2 * np.pi * y_vals / height_rect
    teta = teta.astype(float)
    phi = fi.astype(float)
    # Create 3D coordinates base on teta and phi
    x = (R + r * np.cos(teta)) * np.cos(phi)
    y = (R + r * np.cos(teta)) * np.sin(phi)
    z = r * np.sin(teta)

    # Custom color map
    normalized_z = np.ones(z.size) - 0.5
    colormap = cm.get_cmap('Blues')
    vertices = np.column_stack((x, y, z))
    paths = [vertices]
    collection = Line3DCollection(paths, colors=colormap(normalized_z), linewidths=1)
    ax_3d.add_collection(collection)
    # Custom color
    ax_3d.plot3D(x, y, z, c='green')

    # To rotate the Torus
    ax_3d.view_init(elev=index*5+90, azim=index*2+45)

    # Save picture in mediaum-high quality
    plt.savefig(fr'{dir_name}\frame_{index}.png', dpi=800)
    index += 1


    # slope, intercept = mirror_line(slope, intercept, new_point)
    # starting_point = new_point
    # sides_dict = {0: "Left Side", 1: "Bottom Side", 2: "Right Side", 3: "Up Side"}


    if side_hitten == "Right Side":
        starting_point = [0, new_point[1]]
    elif side_hitten == "Up Side":
        starting_point = [new_point[0], 0]
    elif side_hitten == "Bottom Side":
        starting_point = [new_point[0], height_rect]
    elif side_hitten == "Left Side":
        starting_point = [base_rect, new_point[1]]

    intercept = starting_point[1] - slope * starting_point[0]

    return slope, intercept, starting_point


def torus(R: int, r: int):
    """Draws a Torus given R and r"""
    # Define angle
    teta = np.arange(0., 2 * np.pi + 0.1, 0.1)
    phi = np.arange(0., np.pi + 0.1, 0.1)
    # Create coordinates for 3D graph
    TETA, PHI = np.meshgrid(teta, phi)
    # Define the Torus
    x = (R + r * np.cos(TETA)) * np.cos(PHI)
    y = (R + r * np.cos(TETA)) * np.sin(PHI)
    z = r * np.sin(TETA)

    return x, y, z


# Set style
plt.style.use('dark_background')

# Create the biliard table
base_rect = 1
height_rect = 1

# Torus parameters
# Ring Radius
R = base_rect / (2 * np.pi)
# Tube Radius
r = height_rect / (2 * np.pi)

# Global parameters
index = 0
red_count = 0
anchor_point_3D = list()
intercept_3D = float()
sum_of_segments = list()
initialize_csv()
df_vals = pd.read_csv("vals_to_study.csv", engine='c')
T_i = None

# Show 2D and 3D graphs at the same time
fig = plt.figure(figsize=(10, 5))

# 2D GRAPH
# Place the rectangle
square = plt.Rectangle((0, 0), base_rect, height_rect, edgecolor="white", fill=False, antialiased=True)
ax_2d = fig.add_subplot(121, autoscale_on=False, xlim=(-0.05, base_rect + 0.5), ylim=(-0.05, height_rect + 0.05))
# Remove Axis line
ax_2d.get_xaxis().set_visible(False)
ax_2d.get_yaxis().set_visible(False)
ax_2d.axis('off')
ax_2d.add_patch(square)

# 3D GRAPH
X_torus, Y_torus, Z_torus = torus(R, r)

ax_3d = fig.add_subplot(122, projection='3d')
offset = 0.4
norm = mpl.colors.Normalize(-abs(Z_torus).max(), abs(Z_torus).max())
ax_3d.set_zlim(-abs(Z_torus).max() - offset, abs(Z_torus).max() + offset)
ax_3d.set_axis_off()
# This line is commented, so you can see the path of the ball making the Torus.
# Otherwise, the path and the Torus will be overlapped.
# ax_3d.plot_surface(X_torus, Y_torus, Z_torus, rstride=1, cstride=1, linewidth=0, antialiased=False, norm=norm,
#                    cmap='bwr', edgecolor='none')

# These parameters are for the not periodical path
# slope = 0.69009298006744812514767772881896235048770904541015625
slope = 0.2
# slope = 0.92311850728619326833523928144131787121295928955078125
# slope = float(sympy.GoldenRatio)
# slope = np.pi
starting_point = [0.2, 0.4]
SPAWN_POINT = starting_point
previous_intersection = SPAWN_POINT
intercept = starting_point[1] - slope * starting_point[0]

# Draw line referred to 1D case
x_vals_oneD = np.arange(0, base_rect + 0.001, 0.001)
y_vals_oneD = np.ones_like(x_vals_oneD) * starting_point[1]
ax_2d.plot(x_vals_oneD, y_vals_oneD, color="red")


# Directory to save images
dir_name = "nperiodic"

# Start the animation
ani = animation.FuncAnimation(fig, animate, fargs=(base_rect, height_rect, r,), interval=1000, blit=False)
plt.show()

# If you want to save into .mp4 format:

# FFwriter = animation.FFMpegWriter(fps=60)
# ani.save('animation.mp4', writer=FFwriter)

# But I advise you to save pic for each animation
# and then make a video using the following command:
# ffmpeg -r 30 -i frame_%d.png -c:v libx264 -crf 20 -pix_fmt yuv420p output.mp4

# 30 is number of frames for each seconds
# frame_%d.png in the name for every single photo
