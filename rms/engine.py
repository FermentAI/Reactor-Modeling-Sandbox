
from pyfoomb import Caretaker
import pandas as pd
import numpy as np
import os 
import importlib.util
import inspect

class Model():

    # class to keep track of all model related info at a high level
    # receives directory name from drop down menu and loads corresponding data

    def __init__(self, model_path):
        self.model_path = model_path
        self.params = Vars(self.model_path, 'parameters.csv')
        self.mvars = Vars(self.model_path, 'manipulated_vars.csv')
        self.cvars = None
        self.diagram = None
        self.initial_values_dict = self.get_state_dict()
        self.model_class = self.get_model()
        self.subroutine_class = self.get_subroutine()

        # add rows to keep track of state
        self.state = self.mvars.current[self.mvars.current.State].copy(True)
        self.mvars.current.State = False
        self.state.index = self.state.index.map(lambda x: str(x)[:-1])
        self.state.Label = self.state.Label.map(lambda x: str(x)[8:])
        self.mvars.current = self.mvars.current.append(self.state)
        self.state = self.get_state_df()


    def __import_module(self):
        spec = importlib.util.spec_from_file_location('model', os.path.join(self.model_path, 'model.py'))
        model = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model)
        return model

    def get_params_df(self):
        return self.params.current

    def get_mvars_df(self):
        return self.mvars.current

    def get_model(self):
        try:
            return self.__import_module().MyModel
        except AttributeError:
            raise('Need to define the class "MyModel" in the corresponding directory.')

    def get_subroutine(self):
        try:
            return self.__import_module().MySubroutines
        except AttributeError:
            return None

    def get_all_vars_dict(self):
        return {**self.params.current.Value, **self.mvars.current[~self.mvars.current.State].Value}

    def get_vars_dict(self):
        return {**self.params.current.Value, **self.mvars.current.Value}

    def get_state_dict(self):
        return {**self.mvars.current[self.mvars.current.State].Value}

    def get_state_df(self):
        return self.mvars.current[self.mvars.current.State]

    def set_state_df(self, state): #unused rn
        self.state.update(state)
        return

    def update_mvars_from_dict(self, new_mvars_dict, also_IC = False):
        def _update(new_mvars_dict):
            new_mvars_df = pd.DataFrame.from_dict(new_mvars_dict, orient = 'index', columns = ['Value'])
            new_mvars_df.index.name = 'Var'
            self.mvars.current.update(new_mvars_df)

        _update(new_mvars_dict)
        if also_IC:
            new_mvars_dict = {key+'0': value for key, value in new_mvars_dict.items()}
            _update(new_mvars_dict)



class Vars():
    
    # class to keep track of a set of variables
    # receives model info and listents for changes in dash

    def __init__(self, path, var_file):
        self.path = path
        self.var_file = var_file
        self.default = self.read_vars()
        self.current = self.default
    
    def __update(self, pd):  # TODO
        self.current = pd

    def read_vars(self):
        return pd.read_csv(os.path.join(self.path, self.var_file)).set_index('Var').fillna(False).sort_index()

    def get_vars_dict(self):
        return {**self.current.Value}

class Simulator(Caretaker):

    # wrapper for caretacker
    # keep track of simulation settings
    # keep track of control subroutines?
    # evaluate time-dependent input

    # TODO: simulation settings user can change?

    def __init__(self, model,**kwds):
        super().__init__(
                bioprocess_model_class = model.model_class,
                model_parameters = model.get_vars_dict(),
                initial_values = model.initial_values_dict,
                **kwds)

        
        self.simvars = Vars(os.getcwd(), 'rms/simulator_vars.csv')
        self.model = model

        ti = self.simvars.current.loc['Ti','Value']
        tf = self.simvars.current.loc['Tf','Value']
        n = self.simvars.current.loc['n','Value']
        self.dt = (tf-ti)/n

        self.simvars.current.loc['dt','Value'] = self.dt
        self.time = np.linspace(ti,tf,n) 

        if model.subroutine_class: 
            self.subroutines = model.subroutine_class(model, self)
        else:
            self.subroutines = None

    def run(self): #TODO: beautify

        data = [[] for _ in range(len(self.model.get_state_df()))]

        for t in self.time:
            state = self.model.get_state_dict()
            
            # run any subroutine
            if self.subroutines: self.subroutines._run_all()

            # update state and integrate
            results = self.simulate(np.array([t,t+self.dt]), self.model.get_all_vars_dict())

            # log data
            for i,(r,k) in enumerate(zip(results, state.keys())):
                state[k] = r.values[-1]
                data[i].append(r.values[-1])
            self.model.update_mvars_from_dict(state, also_IC = True)

        return pd.DataFrame(data).T.set_index(self.time, 'Time')

class Subroutine():
    
    # class to keep track of all subrutine related info at a high level
    # receives model and listents for changes in dash

    def __init__(self, model, simulator):
        self.model = model
        self.subrvars = Vars(model.model_path, 'subroutine_vars.csv')
        self.subroutine_vars = self.subrvars.get_vars_dict()
        self.model_parameters = model.get_vars_dict()
        self.model_state = model.get_state_dict()
        self.simulator_vars = simulator.simvars.get_vars_dict()

        self._initialization()

    def _initialization(self):
        'This method should be overwritten by user'
        pass
    
    def _run_all(self):
        self.model_parameters = self.model.get_vars_dict()
        self.model_state = self.model.get_state_dict()

        all_methods = (getattr(self, name) for name in dir(self))
        self.exe_methods = filter(lambda x: not x.__name__.startswith('_') ,filter(inspect.ismethod,all_methods))
        for method in self.exe_methods:
            method()
        
        self.model.update_mvars_from_dict(self.model_parameters)

        

# this dsnt work
# class RMS_Model(BioprocessModel):
#     '''
#     Casting BioprocessModel to have consistent nomenclature
#     '''
#     def __init__(self, **kwds):
#         super(RMS_Model,self).__init__(**kwds)
#         self.model_vars = self._model_parameters