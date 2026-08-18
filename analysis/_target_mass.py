import numpy as np

from app.state import AppState


def target_mass(state: AppState):
    """
    Calculate the masses of clusters consisting of a range of atoms - main and messenger

    Parameters
    ----------
    state: AppState
        session state containing at least the intmass attribute
    
    """
    num_main = np.arange(1, state.intmass.main_num + 1)
    num_messenger = np.arange(0, state.intmass.messenger_num + 1)

    main_mass_array = num_main * state.intmass.main_mass
    messenger_mass_array = num_messenger * state.intmass.messenger_mass

    target_masses = (main_mass_array[:, None] + messenger_mass_array).ravel()
    return np.sort(target_masses)