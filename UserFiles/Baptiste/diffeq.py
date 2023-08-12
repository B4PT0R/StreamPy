import numpy as np
from sympy import Function, Eq, dsolve, Derivative, symbols,latex
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# Set up the differential equation using sympy
t = symbols('t')
y = Function('y')
diff_eq = Eq(Derivative(y(t), t, 2) + Derivative(y(t), t) + y(t) + 1, 0)
solution = dsolve(diff_eq)

def model(t, y):
    # Define the system of differential equations
    y1, y2 = y
    dy1dt = y2
    dy2dt = -y1 - y2 - 1
    return [dy1dt, dy2dt]

# Precompute solutions
T = 10
resolution = 0.5
precomputed_solutions = {}
for y0 in np.arange(-5, 5.1, resolution):
    for y_prime0 in np.arange(-5, 5.1, resolution):
        sol = solve_ivp(model, [-T, T], [y0, y_prime0], t_eval=np.linspace(-T, T, 400))
        key = (round(y0, 1), round(y_prime0, 1))
        precomputed_solutions[key] = sol

def main():
    st.title("Differential Equation Presentation")
    st.write("The differential equation we intend to solve is the following:")
    # Display the differential equation in LaTeX
    st.latex(r"y'' + y' + y + 1 = 0")

    # Display the solution
    st.write("Its general solution is:")
    st.latex(sympy.latex(solution))
    
    st.write("Below is an interactive plot for various initial values of the parameters.")
    # Initialize the plot
    fig, ax = plt.subplots()
    line1, = ax.plot([], [], label='y(t)')
    line2, = ax.plot([], [], label="y'(t)")
    ax.set_xlabel('t')
    ax.set_ylabel('y(t) and y\'(t)')
    ax.legend()

    def draw():
        try:
            y0 = round(y0_widget.value, 1)
            y_prime0 = round(y_prime0_widget.value, 1)
            sol = precomputed_solutions[(y0, y_prime0)]

            line1.set_data(sol.t, sol.y[0])
            line2.set_data(sol.t, sol.y[1])

            ax.relim()
            ax.autoscale_view()

        except:
            pass
        
    y0_widget = st.number_input('Initial position y(0)', value=0.0, on_change=draw, step=resolution)
    y_prime0_widget = st.number_input('Initial velocity y\'(0)', value=0.0, on_change=draw, step=resolution)
    st.pyplot(fig)
    # Initial call to populate the plot
    draw()

main()
