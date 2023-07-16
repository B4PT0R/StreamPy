import numpy as np
import matplotlib.pyplot as plt 

def plot(f):
    X=np.linspace(-5,5,500)
    fig=plt.figure()
    plt.plot(X,f(X))
    st.pyplot(fig)


    
