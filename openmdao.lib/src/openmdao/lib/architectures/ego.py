import os
from tempfile import mkdtemp
import os.path
import shutil

from enthought.traits.api import HasTraits

from openmdao.main.problem_formulation import IArchitecture
from openmdao.main.api import Assembly, Component, Driver, \
     SequentialWorkflow, Case, ExprEvaluator, implements

from openmdao.lib.components.api import MetaModel, ExpectedImprovement, ParetoFilter
from openmdao.lib.surrogatemodels.api import KrigingSurrogate
from openmdao.lib.drivers.api import DOEdriver, Genetic, CaseIteratorDriver, IterateUntil

from openmdao.lib.doegenerators.api import OptLatinHypercube
from openmdao.lib.casehandlers.api import DBCaseRecorder, DBCaseIterator
from openmdao.lib.datatypes.api import Str, Array, Float, Int, Enum


#TODO: Only supports HasObjective,HasParameters - real/contiunous variables        
class EGO(HasTraits): 
    implements(IArchitecture)
    
    initial_DOE_size = Int(default=40, iotype="in",desc="number of initial training points to use")
    sample_iterations = Int(default=40, iotype="in", desc="number of adaptively sampled points to use")
    EI_PI = Enum("EI",values=["EI","PI"],iotype="in",desc="switch to decide between EI or PI for infill criterion")
    min_ei_pi = Float(default=0.001, iotype="in", desc="EI or PI to use for stopping condition of optimization")
    
    def configure(self):    
        self._tdir = mkdtemp()        
        
        self.comp_name = None
        #check to make sure no more than one component is being referenced
        #TODO: possibly wrap multiple components up into an enclosing assembly automatigally? 
        for target,param in self.parent.get_parameters().iteritems():
            comp = param.get_referenced_compnames()
            if len(comp) > 1:
                self.parent.raise_exception('The EGO architecture can only be used on one'
                                            'component at a time, but parameters from %s '
                                            'were added to the problem formulation.'%comp,ValueError)
            elif self.comp_name is None: 
                self.comp_name = comp.pop()
            else:
                comp = comp.pop()                
                if comp != self.comp_name: 
                    self.parent.raise_exception('The EGO architecture can only be used on one'
                                            'component at a time, but parameters from %s '
                                            'were added to the problem formulation.'%([comp[0],self.comp_name],),ValueError)
                
                
        #change name of component to add '_model' to it. 
        #     lets me name the metamodel as the old name
        self.comp= getattr(self.parent,self.comp_name)
        self.comp.name = "%s_model"%self.comp_name
        
        #add in the metamodel
        meta_model = self.parent.add(self.comp_name,MetaModel()) #metamodel now replaces old component with same name
        meta_model.surrogate = {'default':KrigingSurrogate()}
        meta_model.model = self.comp
        
        meta_model_recorder = DBCaseRecorder(os.path.join(self._tdir,'trainer.db'))
        meta_model.recorder = meta_model_recorder
        meta_model.force_execute = True
        
        EI = self.parent.add("EI",ExpectedImprovement())
        self.objective = self.parent.get_objectives().keys()[0]
        EI.criteria = self.objective
        
        pfilter = self.parent.add("filter",ParetoFilter())
        pfilter.criteria = [self.objective]
        pfilter.case_sets = [meta_model_recorder.get_iterator(),]
        pfilter.force_execute = True
        
        #Driver Configuration
        DOE_trainer = self.parent.add("DOE_trainer",DOEdriver())
        DOE_trainer.sequential = True
        DOE_trainer.DOEgenerator = OptLatinHypercube(num_samples=self.initial_DOE_size)
        
        for target in self.parent.get_parameters(): 
            DOE_trainer.add_parameter(target)

        DOE_trainer.add_event("%s.train_next"%self.comp_name)
        
        DOE_trainer.case_outputs = [self.objective]
        DOE_trainer.recorder = DBCaseRecorder(':memory:')
        
        EI_opt = self.parent.add("EI_opt",Genetic())
        EI_opt.opt_type = "maximize"
        EI_opt.population_size = 100
        EI_opt.generations = 10
        EI_opt.selection_method = "tournament"
        
        
        for target in self.parent.get_parameters(): 
            EI_opt.add_parameter(target)
        EI_opt.add_objective("EI.%s"%self.EI_PI)
        EI_opt.force_execute = True
        
        
        retrain = self.parent.add("retrain",Driver())
        retrain.add_event("%s.train_next"%self.comp_name)
        retrain.force_execute = True
        
        iter = self.parent.add("iter",IterateUntil())
        iter.max_iterations = self.sample_iterations
        iter.add_stop_condition('EI.PI <= %s'%self.min_ei_pi)
        
        #Iteration Heirarchy
        self.parent.driver.workflow.add(['DOE_trainer', 'iter'])
        
        DOE_trainer.workflow.add(self.comp_name)
        
        iter.workflow = SequentialWorkflow()
        iter.workflow.add(['filter', 'EI_opt', 'retrain'])
        
        EI_opt.workflow.add([self.comp_name,'EI'])
        retrain.workflow.add(self.comp_name)
        
        #Data Connections
        self.parent.connect("filter.pareto_set","EI.best_case")
        self.parent.connect(self.objective,"EI.predicted_value")
        
    def cleanup(self):
        shutil.rmtree(self._tdir, ignore_errors=True)