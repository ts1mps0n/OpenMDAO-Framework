Setting Up Problems for Automatic Architectures
===============================================

In all the previous examples, first you defined an assembly and then added the ``Discipline 1`` and ``Discipline 2``
components into that assembly. You also added at least one driver (e.g. optimizer) into the assembly. This let you 
set up a specific version of the Sellar Problem that matched up with the structure of how to solve a problem using 
IDF, MDF, or CO. Each example had a different set of optimizers, parameters, constraints, and objectives. 

In OpenMDAO there is a way you can automatically build configure the SellarProblem to be solved with IDF, MDF, or CO. 
Using this automatic formulation will result in a lot less effort on your part. But, before you can use the 
automatic architectures you need to make a small change to how you define the Sellar Problem. You need to create a 
more general description of the Sellar Problem that is independent of how you would solve it with any given 
architecture. 

In OpenMDAO you do this with a special kind of assembly called an *ArchitectureAssembly*. When you define an 
your *ArchitectureAssembly*, in addition to adding the specifc discipline analyses you also specify the 
parameters, objectives, constraints, and coupling variables of the fundamental problem formulation. 

.. testcode:: sellar_architecture_assembly


        from openmdao.main.api import ArchitectureAssembly
        from openmdao.lib.optproblems.api import Discipline1, Discipline2
        
        class SellarProblem(ArchitectureAssembly):
            """ Sellar test problem definition.
            Creates a new Assembly with this problem
                
            Optimal Design at (1.9776, 0, 0) 
            Optimal Objective = 3.18339"""
                
            def configure(self):         
                #add the discipline components to the assembly
                self.add('dis1', Discipline1())
                self.add('dis2', Discipline2())
                
                #START OF MDAO Problem Definition
                #Global Des Vars
                self.add_parameter(("dis1.z1","dis2.z1"),name="z1",low=-10,high=10,start=5.0)
                self.add_parameter(("dis1.z2","dis2.z2"),name="z2",low=0,high=10,start=2.0)
                
                #Local Des Vars 
                self.add_parameter("dis1.x1",low=0,high=10,start=1.0)
                
                #Coupling Vars
                self.add_coupling_var(("dis2.y1","dis1.y1"),name="y1",start=1.0)
                self.add_coupling_var(("dis1.y2","dis2.y2"),name="y2",start=1.0)
                                   
                self.add_objective('(dis1.x1)**2 + dis1.z2 + dis1.y1 + math.exp(-dis2.y2)',name="obj1")
                self.add_constraint('3.16 < dis1.y1')
                self.add_constraint('dis2.y2 < 24.0')


                #END OF Sellar Problem Definition

