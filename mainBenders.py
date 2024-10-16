from pyscipopt import Model, quicksum,Expr, multidict, SCIP_PARAMSETTING, Benders, Benderscut, SCIP_RESULT, SCIP_LPSOLSTAT

    
import numpy as np
import csv
import time
import Benders

#import xlsxwriter 

import xlwt

# tamaños_I = [168]
# tamaños_L = [16, 50, 100]
# tamaños_S = [10, 50, 150]


tamaños_I = [168]
tamaños_L = [16]
tamaños_S = [10]

K = [1,2]

timelim = 7200 #2 horas 
rates = [0.4]
verif = 0.4

#ambulance = [[10,6], [20,11], [35,20]]
ambulance = [[10,6]]
t = 10
tmax = 30
alpha_i = [0.65, 0.2, 0.1, 0.05]

countcsv = 1
       
#book=xlwt.Workbook(encoding="utf-8",style_compression=0)
#sheet = book.add_sheet('Tesis_FirstpartialMPModified_120924', cell_overwrite_ok=True)


#def data_cb(m, where):
#    if where == gp.GRB.Callback.MIPSOL:
#        cur_obj = m.cbGet(gp.GRB.Callback.MIPSOL_OBJ)
#        cur_bd = m.cbGet(gp.GRB.Callback.MIPSOL_OBJBND)
#        #sepa = partialMP.cbGet(GRB.callback.MIP_NODCNT)
#        #sepa2 = partialMP.cbGet(GRB.callback.MIP_ITRCNT)
#        gap = abs((cur_obj - cur_bd) / cur_obj)*100  
#        status = gp.GRB.OPTIMAL
#        #gap = cur_obj - cur_bd
#        # Did objective value or best bound change?
#        # if m._obj != cur_obj or m._bd != cur_bd:
#        #     m._obj = cur_obj
#        #     m._bd = cur_bd
#        #     m._data.append([time.time() - partialMP._start, cur_obj, cur_bd])
#        m._data.append(["time", "best", "best bound", "gap %", "status"])
#        m._data.append([time.time() - partialMP._start, cur_obj, cur_bd, gap, status])



for iconj in range(len(tamaños_I)):
    for jconj in range(len(tamaños_L)):
        for sconj in range(len(tamaños_S)):
            for k in range(len(ambulance)):
            #for rep in range(repeticiones):
                
                initial_time = time.time()
                
                eta = ambulance[k]
    
                #Nombre: Instancias_Prueba_I_L_M_N_S_Rep
                
                
                archivo = open('Instances_DemandFixed_'
                          +str(tamaños_I[iconj])+str('_')
                          +str(tamaños_L[jconj])+str('_')
                          +str(tamaños_S[sconj])
                          + '_' + str(verif) + '_'
                          +'.txt', "r")
                
                len_I = int(archivo.readline())
                len_L = int(archivo.readline())
                len_S = int(archivo.readline())

                # Sets #
                I = []
                for i in range(len_I):
                    I.append(int(i+1))
                    
                L = []
                for i in range(len_L):
                    L.append(int(i+1))
                    
                Demand = []
                for s in range(len_S):
                    Demand.append([])
                    line = archivo.readline().strip().split()
                    for i in range(len_I):
                        Demand[s].append(int(line[i]))
                
                #Scenarios
                S = []
                TotalAccidentes = 0
                auxI = [0, 0]
                for l in range(len_S):
                    count = 0
                    line = archivo.readline().strip().split()
                    #print("line", line)
                    S.append([])
                    for i in range(len(I)):
                        #print("line[i]", line[count])
                        #print("line[i]", line)
                        S[l].append([])
                        for k in range(len(K)):
                            #print("line[count]", line[count])
                            S[l][i].append(int(line[count]))
                            if k == 0:
                                auxI[0] = int(line[count])
                            else:
                                auxI[1] = int(line[count])
                            if count < len(line)-1:
                                count += 1
                        if any(auxI):
                            TotalAccidentes += 1
                            #S[l][i].append(int(line[i+1]))
                #break                   
                #Response times
                r_li = []
                for l in range(len(L)):
                    line = archivo.readline().strip().split()
                    r_li.append([])
                    for i in range(len(I)):
                        r_li[l].append(int(line[i]))   
                    
                     
                cli = []
                for l in range(len(L)):
                    line = archivo.readline().strip().split()
                    cli.append([])
                    for i in range(len(I)):
                        if float(line[i]) == 1:
                            cli[l].append(1)
                        else:
                            cli[l].append(0)
                            
                #break

#                S = [S[0]]
##                I = I[:71]
#                L = L[:5]
                pi = (np.amax(cli)/len(S) + 0.005)
                V = [1,2]
                #alpha_i= [100000 *  i for i in alpha_i]
                ######################################################################
                ######################    partialMP   ####################################
                ######################################################################
                
                presolve = 0
                partialMP = Model("CoverageMP")
                partialMP.setParam('limits/time',timelim) #timelim
                
                varT = "I"
                if(varT == "C"):
                # Create variables #
                    x_vars = {"x(%s,%s)" %(l,k): partialMP.addVar(vtype="I",lb = 0, ub = eta[k-1], name="x(%s,%s)" %(l,k)) for l in L for k in K}                

                
                    # Add constraints
                    
                    boundOfNumberOflocatedAmbulance = {}
                    for k in K:  #number of located ambulances cannot exceed
                        boundOfNumberOflocatedAmbulance[k] = partialMP.addCons(quicksum(x_vars["x(%s,%s)" %(l,k)] for l in L) <= eta[k-1], "c2_"+str(k))
                
                elif(varT == "I"):
                    x_vars = {"x(%s,%s,%s)" %(l,k,n): partialMP.addVar(vtype="B", name="x(%s,%s,%s)" %(l,k,n)) for l in L for k in K for n in range(eta[k-1])}
                    for k in K:
                        sum2 = Expr()    
                        for l in L:
                            for n in range(eta[k-1]-1):
                                partialMP.addCons( x_vars["x(%s,%s,%s)" %(l,k,n)] - x_vars["x(%s,%s,%s)" %(l,k,n+1)] <= 0 , "cI_(%s,%s,%s)" %(l,k,n))
                                sum2+=x_vars["x(%s,%s,%s)" %(l,k,n)]
                                partialMP.addCons(x_vars["x(%s,%s,%s)" %(l,k,n)] <=1)
                                partialMP.addCons(-x_vars["x(%s,%s,%s)" %(l,k,n)] <=0)
                            sum2 += x_vars["x(%s,%s,%s)" %(l,k,eta[k-1]-1)]

                            partialMP.addCons(x_vars["x(%s,%s,%s)" %(l,k,eta[k-1]-1)] <=1)
                            partialMP.addCons(-x_vars["x(%s,%s,%s)" %(l,k,eta[k-1]-1)] <=0)
                        partialMP.addCons(sum2 <= eta[k-1],name =" boundOfNumberOflocatedAmbulance_(%s)"% (k))                                        
                    # Setup of benders

                partialMP.data = x_vars

                partialMP.disablePropagation()
                partialMP.setPresolve(SCIP_PARAMSETTING.OFF)
                partialMP.setBoolParam("misc/allowstrongdualreds", False)
                partialMP.setBoolParam("misc/allowweakdualreds", False)
                partialMP.setBoolParam("benders/copybenders", False)
                partialMP.setBoolParam("benders/cutlpsol",True)
                
                
                #partialMP.writeProblem(trans=False)
                bendersName = "myBenders"
                benderscutName = "myBendersCut"                

                
                myBenders = Benders.ambulanceBenders(partialMP.data,I, L,S,K,cli,alpha_i,eta,pi,bendersName,varT)   
                #myBendersCut = Benders.AmbulanceBendersCut(I, L,S,K,cli,alpha_i,eta,pi,benderscutName,varT)
                
                    
                partialMP.includeBenders(myBenders, bendersName, "benders")    
                #partialMP.includeBenderscut(myBenders, myBendersCut, benderscutName,"benderscut plugin", priority=10000)
                

                partialMP.includeBendersDefaultCuts(myBenders)
                
                
                partialMP.activateBenders(myBenders, len(S)) #len(S))
                partialMP.setBoolParam("constraints/benders/active", True)
                #partialMP.writeProblem(trans=False) 
                partialMP.setBoolParam("constraints/benderslp/active", True)
                partialMP.setBoolParam("benders/myBenders/updateauxvarbound", False)
                #partialMP.setIntParam("constraints/benderslp/proptiming",4)
                lowerBounds = { s :  -alpha_i[0] *sum(1 for i in range(len(I)) if (S[s][i-1][0] + S[s][i-1][1] > 0) )/len(S) for s in range(len(S))}
                #partialMP.updateBendersLowerbounds(lowerBounds, myBenders)

                partialMP.writeProblem(trans=False) 
             
                partialMP.optimize()

                if(varT == "C"):
                    bestsol = partialMP.getBestSol()
                    x_value={}
                    for l in L:
                        for k in K:
                    
                            x_value[l,k] = partialMP.getVal(x_vars["x(%s,%s)" %(l,k)])
                            print("(%s,%s) : %s" % (l,k,x_value[l,k]))
                       
                    print(myBenders.EvaluateForReal(x_value))
##                 

                
                #partialMP.setupBendersSubproblem(0, myBenders, partialMP.getBestSol())
                
                #myBenders.subproblems[0].solveProbingLP()    
                #partialMP.printStatistics()
                
                #myBenders.freeBendersSubproblems()  
                #myBenders.subproblems[0].writeProblem(trans=True)            
                #partialMP.printStatistics()   
                #partialMP.freeBendersSubproblems()
                
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                
