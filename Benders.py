from pyscipopt import  Model, quicksum,Expr, multidict, SCIP_PARAMSETTING, Benders, Benderscut, SCIP_RESULT, SCIP_LPSOLSTAT, Branchrule
import time

def print_Cons(cons):
     tt = ""
     for key, ob in cons.expr.terms.items():
          tt += str(round(ob,4)) + str(key.vartuple[0]) + " + " 
     print(tt + " >=  " + str(cons._rhs))

class ambulanceBenders(Benders):

########################################################################## INIT ####################################################################
     def __init__(self,masterVarDict,I, L,S,K,cli,alpha_i,eta,pi,name,varT):
          super(ambulanceBenders, self).__init__()
          self.mpVardict = masterVarDict
          self.I, self.L, self.S, self.K, self.cli, self.alpha_i, self.eta, self.pi = I, L, S, K, cli, alpha_i, eta,pi
          self.name = name  # benders name
          self.subproblems = {}
          self.varT = varT
          
          self.c_bound_on_location = [None]*len(S)
          self.c_total_1 = [None]*len(S)
          self.c_total_2 = [None]*len(S)
          self.c_total_late_1 = [None]*len(S)
          self.c_total_late_2 = [None]*len(S)
          self.c_partial_1 = [None]*len(S)
          self.c_partial_2 = [None]*len(S)
          self.c_partial_3=[None]*len(S)
          self.c_partial_late_1 = [None]*len(S)
          self.c_partial_late_2 = [None]*len(S)
          self.c_gamma = [None]*len(S)
          self.c_one = [None]*len(S)
          self.upperbounds = [{}]*len(S)
          self.lowerbounds = [{}]*len(S)
          self.x_vars = [{}] * len(S)
     
########################################################################## CREATE SUBPROBLEMS #####################################################
     def benderscreatesub(self, probnumber):
     
          print("Building subproblem : " + str(probnumber))
          subprob = Model("AmbulanceScenario_" + str(probnumber))
          subprob.setPresolve(SCIP_PARAMSETTING.OFF)
          subprob.disablePropagation()

          #Variables
          self.x_vars[probnumber] = {}
          self.x_vars[probnumber] = {(0,l,k): subprob.addVar(vtype="I", name="x(%s,%s)" %(l,k)) for l in self.L for k in self.K}
          for l in self.L:
            for k in self.K:
                self.upperbounds[probnumber][0,l,k] = subprob.addCons(self.x_vars[probnumber][0,l,k]<= self.eta[k-1])
                self.lowerbounds[probnumber][0,l,k] = subprob.addCons(-self.x_vars[probnumber][0,l,k] <= 0)
                
          y_vars ={}
          
          for l in self.L:
            for i in self.I:
                if self.S[probnumber][i-1][0] != 0:
                    y_vars[(1,l,1,i)] = subprob.addVar(vtype=self.varT, name="dispacthed"+str('_')+str(l)+str('_')+str(1)+str('_')+str(i)+"_"+str(probnumber))
                
                if self.S[probnumber][i-1][0]+self.S[probnumber][i-1][1] > 0:
                    y_vars[(1,l,2,i)] = subprob.addVar(vtype=self.varT, name="dispacthed"+str('_')+str(l)+str('_')+str(2)+str('_')+str(i)+"_"+str(probnumber))
          
          for l in self.L:
            for i in self.I:
                for k in self.K:
                    if(self.S[probnumber][i-1][0]  +  self.S[probnumber][i-1][1] > 0 ):
                        self.upperbounds[probnumber][1,l,k,i] = subprob.addCons(y_vars[1,l,k,i] <= self.eta[0]+self.eta[1] )
                        self.lowerbounds[probnumber][1,l,k,i] = subprob.addCons(-y_vars[1,l,k,i] <= 0 )                 
              
          f_vars = { (2,i) : subprob.addVar(vtype=self.varT , name="Total"+str('_')+str(i)+"_"+str(probnumber)) for i in self.I if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0}
          for i in self.I :
            if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0:
                self.upperbounds[probnumber][2,i]= subprob.addCons(f_vars[2,i] <= 1)    
                self.lowerbounds[probnumber][2,i]= subprob.addCons(-f_vars[2,i] <= 0)
                 
          g_vars = { (3,i) : subprob.addVar(vtype=self.varT, name="Total_late"+str('_')+str(i) + "_"+str(probnumber)) for i in self.I if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0}
          
          for i in self.I :
            if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0:
                self.upperbounds[probnumber][3,i]= subprob.addCons(g_vars[3,i] <= 1)    
                self.lowerbounds[probnumber][3,i]= subprob.addCons(-g_vars[3,i] <= 0)
          
          h_vars = { (4,i) : subprob.addVar(vtype=self.varT,  name="Partial"+str('_')+str(i)+"_"+str(probnumber)) for i in self.I if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0}
          
          for i in self.I :
            if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0:
                self.upperbounds[probnumber][4,i]= subprob.addCons(h_vars[4,i] <= 1 )    
                self.lowerbounds[probnumber][4,i]= subprob.addCons(-h_vars[4,i] <=0)
                     
          w_vars = { (5,i) : subprob.addVar(vtype=self.varT,  name="Partial_late"+str('_')+str(i)+"_"+str(probnumber)) for i in self.I if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0}  
          
          for i in self.I :
            if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0:
                self.upperbounds[probnumber][5,i]= subprob.addCons(w_vars[5,i] <= 1)   
                self.lowerbounds[probnumber][5,i]= subprob.addCons(-w_vars[5,i] <= 0)
          
          gamma_vars = { (6,i) : subprob.addVar(vtype=self.varT,  name="Null"+str('_')+str(i)+"_"+str(probnumber)) for i in self.I if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0} 
          
          for i in self.I :
            if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0:
                self.upperbounds[probnumber][6,i]= subprob.addCons(gamma_vars[6,i]<=1)
                self.lowerbounds[probnumber][6,i]= subprob.addCons(-gamma_vars[6,i] <= 0)
          
          #objective
          
          subprob.setObjective(quicksum((-self.alpha_i[0]*f_vars[2,i] - self.alpha_i[1]*g_vars[3,i] - self.alpha_i[2]*h_vars[4,i] - self.alpha_i[3]*w_vars[5,i] + self.pi*gamma_vars[6,i])/len(self.S)  for i in self.I if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1]) > 0),"minimize")
          
          ##Constraints   ######## Reduced cost 1
          self.c_bound_on_location[probnumber]={}
          for l in self.L:
                self.c_bound_on_location[probnumber][l,1] = subprob.addCons(quicksum(y_vars[1,l,1,i] for i in self.I if self.S[probnumber][i-1][0]  != 0)  <= self.x_vars[probnumber][0,l,1], name="boundL_"+str(l)+"_"+str(1)+"_"+str(probnumber))
                
                self.c_bound_on_location[probnumber][l,2] = subprob.addCons(quicksum(y_vars[1,l,2,i] for i in self.I if self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] != 0)  <= self.x_vars[probnumber][0,l,2], name="boundL_"+str(l)+"_"+str(2)+"_"+str(probnumber))
          
          #Total 
          self.c_total_1[probnumber] = {}
          for i in self.I:
            if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0) and (self.S[probnumber][i-1][0] != 0):
                self.c_total_1[probnumber][i]= subprob.addCons((self.S[probnumber][i-1][0]+self.S[probnumber][i-1][1])*f_vars[2,i] <= quicksum(self.cli[l-1][i-1]*y_vars[1,l,1,i] + self.cli[l-1][i-1]*y_vars[1,l,2,i] for l in self.L), "c4"+str(i)+"_"+str(probnumber))   
          
          
          self.c_total_2[probnumber] = {}
          for i in self.I:
            if ( self.S[probnumber][i-1][1] > 0 ):
                self.c_total_2[probnumber][i] = subprob.addCons(self.S[probnumber][i-1][1]*f_vars[2,i] <= quicksum(self.cli[l-1][i-1]*y_vars[1,l,2,i] for l in self.L), "c4_1_"+"_"+str(i) + "_" + str(probnumber))
        
       

          # Total late
          
          
          self.c_total_late_1[probnumber] ={}
          for i in self.I:
            if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0) and (self.S[probnumber][i-1][0] != 0):
                self.c_total_late_1[probnumber][i]=subprob.addCons((self.S[probnumber][i-1][0]+self.S[probnumber][i-1][1])*g_vars[3,i] <= quicksum(y_vars[1,l,1,i] + y_vars[1,l,2,i] for l in self.L), "c5"+"_"+str(i)+"_"+str(probnumber))
          
    
          self.c_total_late_2[probnumber] = {}
          for i in self.I:
            if ( self.S[probnumber][i-1][1] > 0 ):
                self.c_total_late_2[probnumber][i] = subprob.addCons(self.S[probnumber][i-1][1]*g_vars[3,i] <= quicksum(y_vars[1,l,2,i] for l in self.L), "c5_1_"+str(i)+"_"+str(probnumber)) 
          

          # Partial 
          

          
          ############ Reduced cost 2
          
          #Partial 1
          
          self.c_partial_1[probnumber]={}
          for i in self.I:
            sum_h2 = Expr()
            if self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0:
                if self.S[probnumber][i-1][0] != 0:
                    sum_h2 += quicksum(self.cli[l-1][i-1]*y_vars[1,l,1,i] + self.cli[l-1][i-1]*y_vars[1,l,2,i] for l in self.L)
                    self.c_partial_1[probnumber][i] = subprob.addCons(h_vars[4,i] <= (self.S[probnumber][i-1][0]+self.S[probnumber][i-1][1]) - sum_h2, "c6_"+str(i)+"_"+str(probnumber))
                elif self.S[probnumber][i-1][1] != 0 and self.S[probnumber][i-1][0] == 0:
                    sum_h2 += quicksum(self.cli[l-1][i-1]*y_vars[1,l,2,i] for l in self.L)
                    self.c_partial_1[probnumber][i] = subprob.addCons(h_vars[4,i] <= (self.S[probnumber][i-1][0]+self.S[probnumber][i-1][1]) - sum_h2, "c6_"+str(i)+"_"+str(probnumber))
                
           ############ Redecued cost 3     
                           
           #Partial 2                 

          self.c_partial_2[probnumber] ={}
          for i in self.I:
            for k in self.K:
                for l in self.L:
                    if self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0:
                        if self.cli[l-1][i-1] == 0:
                            if k == 1:
                                 self.c_partial_2[probnumber][i,k,l]= subprob.addCons(self.S[probnumber][i-1][k-1]*h_vars[4,i] + y_vars[1,l,k,i] <= self.S[probnumber][i-1][k-1], "c7_"+str(i)+"_"+str(k)+"_"+str(l)+"_"+str(probnumber))
                            else:
                                 self.c_partial_2[probnumber][i,k,l] =subprob.addCons(self.S[probnumber][i-1][k-1]*h_vars[4,i] + y_vars[1,l,k,i] <= self.S[probnumber][i-1][k-1], "c7_"+str(i)+"_"+str(k)+"_"+str(l)+"_"+str(probnumber))
                                 
                                 
         # Partial 3
          self.c_partial_3[probnumber] = {}
          for i in self.I:
            if self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0:
                if self.S[probnumber][i-1][0] != 0:
                    sum_w2 = quicksum(self.cli[l-1][i-1]*(y_vars[1,l,1,i] + y_vars[1,l,2,i]) for l in self.L)
                    self.c_partial_3[probnumber][i] = subprob.addCons(h_vars[4,i] <= sum_w2, "chmax_%s_%s" %(i,probnumber))
                
                elif self.S[probnumber][i-1][1] != 0:
                    sum_w2 = quicksum(self.cli[l-1][i-1]*y_vars[1,l,2,i] for l in self.L)
                    self.c_partial_3[probnumber][i] = subprob.addCons(h_vars[4,i] <= sum_w2, "chmax_%s_%s" %(i,probnumber))
         
         
                                        
          # Partial late
          
          # Reduced cost 4
          self.c_partial_late_1[probnumber]={}
          for i in self.I:
            sum_w2 = Expr()
            if self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0:
                if self.S[probnumber][i-1][0] != 0:
                    sum_w2 += quicksum(y_vars[1,l,1,i] + y_vars[1,l,2,i] for l in self.L)
                    self.c_partial_late_1[probnumber][i] = subprob.addCons(w_vars[5,i] <= (self.S[probnumber][i-1][0]+self.S[probnumber][i-1][1]) - sum_w2, "c8_"+str(i)+"_"+str(probnumber))
                    
                elif S[probnumber][i-1][1] != 0:
                    sum_w2 += quicksum(y_vars[1,l,2,i] for l in self.L)
                    self.c_partial_late_1[probnumber][i] = subprob.addCons(w_vars[5,i] <= (self.S[probnumber][i-1][0]+self.S[probnumber][i-1][1]) - sum_w2, "c8_"+str(i)+"_"+str(probnumber))
                            
          #no rdc
          self.c_partial_late_2[probnumber] = {}
          for i in self.I:
            sum_w2 = Expr()
            if self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0:
                if self.S[probnumber][i-1][0] != 0:
                    sum_w2 += quicksum(y_vars[1,l,1,i] + y_vars[1,l,2,i] for l in self.L)
                    self.c_partial_late_2[probnumber][i] = subprob.addCons(w_vars[5,i] <= sum_w2, "c9_"+str(i)+"_"+str(probnumber))
                    
                elif self.S[probnumber][i-1][1] != 0:
                    sum_w2 += quicksum(y_vars[1,l,2,i] for l in self.L)
                    self.c_partial_late_2[probnumber][i] = subprob.addCons(w_vars[5,i] <= sum_w2, "c9_"+str(i)+"_"+str(probnumber))
                   
                        
          # Gamma
          
          #reduced cost 5 

          self.c_gamma[probnumber] = {}
          for i in self.I:
            sum_gamma = Expr()
            if self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0:
                if self.S[probnumber][i-1][0] != 0:
                    sum_gamma -= quicksum(y_vars[1,l,1,i] + y_vars[1,l,2,i] for l in self.L)
                elif self.S[probnumber][i-1][1] != 0:
                    sum_gamma -= quicksum(y_vars[1,l,2,i] for l in self.L)
                self.c_gamma[probnumber][i] = subprob.addCons(sum_gamma - gamma_vars[6,i] <= -1, "c_11_"+str(i) +"_"+ str(probnumber))

          self.c_one[probnumber] = {}
          
          #reduced cost 6

          for i in self.I:
            if (self.S[probnumber][i-1][0] + self.S[probnumber][i-1][1] > 0):
                self.c_one[probnumber][i] = subprob.addCons(f_vars[2,i] + g_vars[3,i] + h_vars[4,i] + w_vars[5,i] + gamma_vars[6,i] <= 1, "c_12_"+str(i)+"_"+str(probnumber))

          dic_x = {value.name : value for key,value in self.x_vars[probnumber].items() }
          dic_y = {value.name : value for key,value in y_vars.items()}
          dic_f = {value.name : value for key,value in f_vars.items()}
          dic_g = {value.name : value for key,value in g_vars.items()}
          dic_h = {value.name : value for key,value in h_vars.items()}
          dic_w = {value.name : value for key,value in w_vars.items()}
          dic_gamma = {value.name : value for key , value in gamma_vars.items()}
          
          #subprob.writeProblem()
          
          
          
          subprob.data = dic_x| dic_y| dic_f| dic_g| dic_h| dic_w| dic_gamma
          self.model.addBendersSubproblem(self, subprob)

          self.subproblems[probnumber] = subprob     #### THIS GUY MAY ACT WEIRD

############################################################################ GET VARIABLE #############################################################

     def bendersgetvar(self, variable, probnumber):  
          #"x"+str(l)+"_"+"k"
#          name = ""
#          print(variable.name)
#          if(variable.name[0] =="x"):
#                name = (0,variable.name[1],variable.name[3])
#          elif(variable.name[0] =="d"):
#                name = (1,,)
#          elif(variable.name[0] =="T" and variable.name[6] =="l"):
#                name = (3,,)
#          elif(variable.name[0] =="T"):
#                name = (2,,)
#          elif(variable.name[0] == "P" and  variable.name[8] =="l" ):
#                name = (5,,)
#          elif(variable.name[0] =="P"):
#                name = (4,,)
#          elif(variable.name[0] =="N"):
#                name = (6,,)
#          

          try:
                if probnumber == -1:  # convert to master variable
                     mapvar = self.mpVardict[variable.name]
                else:
                     mapvar = self.subproblems[probnumber].data[variable.name]
                     
          except KeyError:
                mapvar = None
          return {"mappedvar": mapvar}

######################################################################## SOLVE SUBPROBLEMS ############################################################
     def benderssolvesubconvex(self, solution, probnumber, onlyconvex):
          result_dict = {}
          
          self.model.setupBendersSubproblem(probnumber, self, solution) 

          self.subproblems[probnumber].solveProbingLP()

          subprob = self.model.getBendersSubproblem(probnumber, self)  
          #assert self.subproblems[probnumber].getObjVal() ==subprob.getObjVal()
          
          #subprob.updateBendersLowerbounds( -self.pi * len(self.I), self)
          
          objective = subprob.infinity()
          result = SCIP_RESULT.DIDNOTRUN
          lpsolstat = self.subproblems[probnumber].getLPSolstat()
          if lpsolstat == SCIP_LPSOLSTAT.OPTIMAL:
              objective = self.subproblems[probnumber].getObjVal()
              result = SCIP_RESULT.FEASIBLE
          elif lpsolstat == SCIP_LPSOLSTAT.INFEASIBLE:

              objective = self.subproblems[probnumber].infinity()
              result = SCIP_RESULT.INFEASIBLE
          elif lpsolstat == SCIP_LPSOLSTAT.UNBOUNDEDRAY:

              objective = self.subproblems[probnumber].infinity()
              result = SCIP_RESULT.UNBOUNDED
         

          result_dict["objective"] = objective
          result_dict["result"] = result

                               
          return result_dict
          
     def bendersfreesub(self, probnumber):
          if self.subproblems[probnumber].inProbing():
              self.subproblems[probnumber].endProbing()



class AmbulanceBendersCut(Benderscut):

    def __init__(self,I, L,S,K,cli,alpha_i,eta,pi,name,varT):
          self.I, self.L, self.S, self.K, self.cli, self.alpha_i, self.eta, self.pi = I, L, S, K, cli, alpha_i, eta,pi
          self.name = name  # benders name
          self.subproblems = {}
          self.varT = varT
      


    def benderscutexec(self, solution, probnumber, enfotype):
        subprob = self.model.getBendersSubproblem(probnumber, benders=self.benders)
        membersubprob = self.benders.subproblems[probnumber]
        
        if self.model.checkBendersSubproblemOptimality(solution, probnumber, benders=self.benders):
            return {"result" : SCIP_RESULT.FEASIBLE}
      

        Ax = Expr()
        linExpr = Expr()
        linExpr += self.model.getBendersAuxiliaryVar(probnumber,self.benders)
        
        
#        
#        ##RDC 1

        optSub = 0
        for key,value in self.benders.c_bound_on_location[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getLhs(value)
        print( "1 "+ str(optSub))
        for key,value in self.benders.c_total_1[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "2 "+ str(optSub))
        for key,value in self.benders.c_total_2[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "3 "+ str(optSub))
        for key,value in self.benders.c_total_late_1[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "4 "+ str(optSub))
        for key,value in self.benders.c_total_late_2[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "5 "+ str(optSub))
        for key,value in self.benders.c_partial_1[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "6 "+ str(optSub))        
        for key,value in self.benders.c_partial_2[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "7"+ str(optSub))
        for key,value in self.benders.c_partial_3[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "8 "+ str(optSub))        
        for key,value in self.benders.c_partial_late_1[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "9 "+ str(optSub))        
        for key,value in self.benders.c_partial_late_2[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "10 "+ str(optSub))        
        for key,value in self.benders.c_gamma[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "11 "+ str(optSub))
        for key,value in self.benders.c_one[probnumber].items():
            optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "12 "+ str(optSub))
        for key,value in self.benders.upperbounds[probnumber].items():
            if(key[0] != 0):
                optSub+= subprob.getDualsolLinear(value) * subprob.getRhs(value)
        print( "13 "+ str(optSub))
        for key,value in self.benders.lowerbounds[probnumber].items():
            if(key[0] != 0):
                optSub+= subprob.getDualsolLinear(value) * subprob.getLhs(value)
        print( "14 "+ str(optSub))
        

        
        
        uAx = 0
        
        #x variables bounds
        for l in self.L:
            for k in self.K:
                Ax+=-subprob.getDualsolLinear(self.benders.upperbounds[probnumber][0,l,k])*self.model.getBendersVar(self.benders.subproblems[probnumber].data[self.benders.x_vars[probnumber][0,l,k].name],self.benders)
                Ax+=subprob.getDualsolLinear(self.benders.lowerbounds[probnumber][0,l,k])*self.model.getBendersVar(self.benders.subproblems[probnumber].data[self.benders.x_vars[probnumber][0,l,k].name],self.benders)
                Ax+=subprob.getDualsolLinear(self.benders.c_bound_on_location[probnumber][l,k]) * self.model.getBendersVar(self.benders.subproblems[probnumber].data[self.benders.x_vars[probnumber][0,l,k].name],self.benders)
                
                #uAx+=subprob.getDualsolLinear(self.benders.upperbounds[probnumber][0,l,k])*self.model.getVal(self.benders.subproblems[probnumber].data[self.benders.x_vars[probnumber][0,l,k].name])
                #uAx+=-subprob.getDualsolLinear(self.benders.lowerbounds[probnumber][0,l,k])*self.model.getVal(self.benders.subproblems[probnumber].data[self.benders.x_vars[probnumber][0,l,k].name])
                uAx+=subprob.getDualsolLinear(self.benders.c_bound_on_location[probnumber][l,k])*self.model.getVal(self.benders.subproblems[probnumber].data[self.benders.x_vars[probnumber][0,l,k].name])

       

        c = self.model.addCons(linExpr + Ax >= subprob.getObjVal()) ###subprob.getObjVal() )   # subprob.getObjVal()-uAx)
        #print_Cons(linExpr + Ax  >= optSub)
        self.model.writeProblem(trans=True)
        
        return {"result" : SCIP_RESULT.CONSADDED}
        




