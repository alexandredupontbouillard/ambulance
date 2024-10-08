# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 14:53:51 2024

@author: beatr
"""

######################################################################
######################  INSTANCES ####################################
######################################################################

from pyscipopt import *
import numpy as np
import csv
import time
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
       
book=xlwt.Workbook(encoding="utf-8",style_compression=0)
sheet = book.add_sheet('Tesis_FirstModelModified_120924', cell_overwrite_ok=True)

#def data_cb(m, where):
#    if where == gp.GRB.Callback.MIPSOL:
#        cur_obj = m.cbGet(gp.GRB.Callback.MIPSOL_OBJ)
#        cur_bd = m.cbGet(gp.GRB.Callback.MIPSOL_OBJBND)
#        #sepa = model.cbGet(GRB.callback.MIP_NODCNT)
#        #sepa2 = model.cbGet(GRB.callback.MIP_ITRCNT)
#        gap = abs((cur_obj - cur_bd) / cur_obj)*100  
#        status = gp.GRB.OPTIMAL
#        #gap = cur_obj - cur_bd
#        # Did objective value or best bound change?
#        # if m._obj != cur_obj or m._bd != cur_bd:
#        #     m._obj = cur_obj
#        #     m._bd = cur_bd
#        #     m._data.append([time.time() - model._start, cur_obj, cur_bd])
#        m._data.append(["time", "best", "best bound", "gap %", "status"])
#        m._data.append([time.time() - model._start, cur_obj, cur_bd, gap, status])



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
                
                # Other parameters #
                #pi = 100
                #S = [S[0]]
                pi = np.amax(cli)/len(S) + 0.005
                V = [1,2]
                    
                ######################################################################
                ######################    MODEL   ####################################
                ######################################################################
                
                presolve = 0
        
                model = Model("PartialRateCoverage")
                #gp.setParam("Cuts",0)
                model.setParam('limits/time',timelim) #timelim
                
#                model._obj = None
#                model._bd = None
#                model._data = []
#                model._start = time.time()
#                
                # Create variables #
                x_vars = {}
                cantVarX = 0
                for l in L:
                    for k in K:
                        x_vars[l,k] = model.addVar(vtype="I", lb = 0, ub = eta[k-1], 
                                         name="located "+str(l)+str(' ')+str(k))
                        cantVarX += 1
                        
                        
                y_vars = {}    
                cantVarY = 0
                
                vv = "C"
                
                for s in range(len(S)):        
                    for l in L:
                        for i in I:
                            if S[s][i-1][0] != 0:
                                y_vars[s+1,l,1,i] = model.addVar(vtype=vv,lb = 0, ub = eta[0],
                                                name="dispatched "+str(s+1)+str(' ')+str(l)+str(' ')+str(1)+str(' ')+str(i))
                                cantVarY += 1
                                
                                y_vars[s+1,l,2,i] = model.addVar(vtype=vv, lb = 0, ub = eta[0] + eta[1],
                                                name="dispatched "+str(s+1)+str(' ')+str(l)+str(' ')+str(2)+str(' ')+str(i))
                                cantVarY += 1
                                
                            if S[s][i-1][1] != 0 and S[s][i-1][0] == 0:
                                y_vars[s+1,l,2,i] = model.addVar(vtype=vv, lb = 0,ub = eta[0] + eta[1],
                                                name="dispatched "+str(s+1)+str(' ')+str(l)+str(' ')+str(2)+str(' ')+str(i))
                                cantVarY += 1
    
                
                f_vars = {}  ## total
                cantVarAlpha = 0
                for s in range(len(S)):
                    for i in I:
                        if (S[s][i-1][0] + S[s][i-1][1]) > 0:
                            f_vars[s+1,i] = model.addVar(vtype=vv, lb = 0, ub = 1,                                 
                                                           name="Total "+str(s+1)+str(' ')+str(i))
                            cantVarAlpha += 1
                            
                
                g_vars = {}  ## total late
                cantVarBeta = 0
                for s in range(len(S)):
                    for i in I:
                        if (S[s][i-1][0] + S[s][i-1][1]) > 0:
                            g_vars[s+1,i] = model.addVar(vtype=vv, lb = 0, ub = 1,   
                                                      name="Total late "+str(s+1)+str(' ')+str(i))
                            cantVarBeta += 1
                            
                
                h_vars = {}  ## partial
                cantVarDelta = 0
                for s in range(len(S)):
                    for i in I:
                        if (S[s][i-1][0] + S[s][i-1][1]) > 0:
                            #h_vars[s+1,i] = model.addVar(vtype=GRB.BINARY, ub = 0,
                            h_vars[s+1,i] = model.addVar(vtype=vv, lb = 0, ub = 1,   
                                                      name="Partial "+str(s+1)+str(' ')+str(i))
                            cantVarDelta += 1
                       
                
                w_vars = {}   ## partial late
                cantVarPhi = 0
                for s in range(len(S)):
                    for i in I:
                        if (S[s][i-1][0] + S[s][i-1][1]) > 0:
                            #w_vars[s+1,i] = model.addVar(vtype=GRB.BINARY, ub=0, 
                            w_vars[s+1,i] = model.addVar(vtype=vv,lb = 0, ub = 1,   
                                                      name="Partial late "+str(s+1)+str(' ')+str(i))
                            cantVarPhi += 1
                       
                
                gamma_vars = {} ## null
                cantVarGamma = 0
                for s in range(len(S)):
                    for i in I:
                        if (S[s][i-1][0] + S[s][i-1][1]) > 0:
                            gamma_vars[s+1,i] = model.addVar(vtype=vv, lb = 0, ub = 1,    
                                                     name="Null "+str(s+1)+str(' ')+str(i))
                            cantVarGamma += 1
                       
                ##Objective function 
                obj = Expr()
                for s in range(len(S)):
                    for i in I:
                        if (S[s][i-1][0] + S[s][i-1][1]) > 0:
                            #obj += 0
                            obj += (-alpha_i[0]*f_vars[s+1,i] - alpha_i[1]*g_vars[s+1,i] - alpha_i[2]*h_vars[s+1,i] -alpha_i[3]*w_vars[s+1,i] + pi*gamma_vars[s+1,i]) * (1/len(S))
                model.setObjective(obj, "minimize")  
    
                
                # Add constraints
                
                #####FAKE CONSTRAINTS
#                for l in L:
#                    for k in K:
#                        if(l ==1 and k==1):
#                               model.addCons(x_vars[l,k] ==10)
#                        elif(l ==1 and k==2):
#                            model.addCons(x_vars[l,k] ==6)    
#                #################
                
                for k in K:
                        model.addCons(quicksum(x_vars[l,k] for l in L) <= eta[k-1], "c2"+str(k))
                for s in range(len(S)):
                    
                    # Restricción 2: No localizar más ambulancias de las disponibles en el sistema
                    
                    
                    # Restricción 3: No enviar más ambulancias de las localizadas para k = 1
                    
                    for l in L:
                        amb1 = Expr()
                        for i in I:
                            if S[s][i-1][0] != 0:                            
                                amb1 += y_vars[s+1,l,1,i]
                        model.addCons(amb1 <= x_vars[l,1], "c3"+str(l))
                   
                        
                   
                    # Restricción 3_1: No enviar más ambulancias de las localizadas para k = 2
                    
                    
                    
                    for l in L:
                        amb2 = Expr()
                        for i in I:
                            if S[s][i-1][0] != 0 or S[s][i-1][1] != 0:
                                amb2 += y_vars[s+1,l,2,i]  
                        model.addCons(amb2 <= x_vars[l,2], "c3_1"+str(i)+str(l))
                        

                    
                        
                    
                    # Restricción 4: f (total)
                    
                    for i in I:
                        sum_f2 = Expr()
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            if S[s][i-1][0] != 0:
                                sum_f2 += quicksum(cli[l-1][i-1]*y_vars[s+1,l,1,i] + cli[l-1][i-1]*y_vars[s+1,l,2,i] for l in L)
                                model.addCons((S[s][i-1][0]+S[s][i-1][1])*f_vars[s+1,i] <= sum_f2, "c4")
                                
                    # Restricción 4_1: f (total)
                    
                    for i in I:
                        sum_f2 = Expr()
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            if S[s][i-1][1] != 0:
                                sum_f2 += quicksum(cli[l-1][i-1]*y_vars[s+1,l,2,i] for l in L)
                                model.addCons(S[s][i-1][1]*f_vars[s+1,i] <= sum_f2, "c4_1")
                
                    # Restricción 5: g (total late)
                    
                    for i in I:
                        sum_g2 = Expr()
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            if S[s][i-1][0] != 0:
                                sum_g2 += quicksum(y_vars[s+1,l,1,i] + y_vars[s+1,l,2,i] for l in L)
                                model.addCons((S[s][i-1][0]+S[s][i-1][1])*g_vars[s+1,i] <= sum_g2, "c5")
                            
                    #Restricción 5_1: g (total late)
                    
                    for i in I:
                        sum_g2 = Expr()
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            if S[s][i-1][1] != 0:
                                sum_g2 += quicksum(y_vars[s+1,l,2,i] for l in L)
                                model.addCons(S[s][i-1][1]*g_vars[s+1,i] <= sum_g2, "c5_1")        
                  
           
                    # Restricción 6: h (partial)
                    
                    for i in I:
                        sum_h2 = Expr()
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            if S[s][i-1][0] != 0:
                                sum_h2 += quicksum(cli[l-1][i-1]*y_vars[s+1,l,1,i] + cli[l-1][i-1]*y_vars[s+1,l,2,i] for l in L)
                                model.addCons(h_vars[s+1,i] <= (S[s][i-1][0]+S[s][i-1][1]) - sum_h2, "c6")
                            elif S[s][i-1][1] != 0 and S[s][i-1][0] == 0:
                                sum_h2 += quicksum(cli[l-1][i-1]*y_vars[s+1,l,2,i] for l in L)
                                model.addCons(h_vars[s+1,i] <= (S[s][i-1][0]+S[s][i-1][1]) - sum_h2, "c6")
                           
                                
                    # Restricción 7: h (partial) 
                    
                    for i in I:
                        for k in K:
                            for l in L:
                                if S[s][i-1][0] + S[s][i-1][1] > 0:
                                    if cli[l-1][i-1] == 0:
                                        if k == 1:
                                            model.addCons(S[s][i-1][k-1]*h_vars[s+1,i] + y_vars[s+1,l,k,i] <= S[s][i-1][k-1], "c7")
                                        else:
                                            model.addCons(S[s][i-1][k-1]*h_vars[s+1,i] + y_vars[s+1,l,k,i] <= S[s][i-1][k-1], "c7")
                     # Restricción 8: h (partial)                        
                    for i in I:
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            #sum_w2=Expr()
                            if S[s][i-1][0] != 0:
                                sum_w2 = quicksum(cli[l-1][i-1]*(y_vars[s+1,l,1,i] + y_vars[s+1,l,2,i]) for l in L)
                                cons = model.addCons(h_vars[s+1,i] <= sum_w2, "chmax")
                                
                            elif S[s][i-1][1] != 0:
                                sum_w2 = quicksum(cli[l-1][i-1]*y_vars[s+1,l,2,i] for l in L)
                                cons = model.addCons(h_vars[s+1,i] <= sum_w2, "chmax")
                                
                                            
                            
                    # Restricción 9: w (partial late)
                    
                    for i in I:
                        sum_w2 = Expr()
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            if S[s][i-1][0] != 0:
                                sum_w2 += quicksum(y_vars[s+1,l,1,i] + y_vars[s+1,l,2,i] for l in L)
                                model.addCons(w_vars[s+1,i] <= (S[s][i-1][0]+S[s][i-1][1]) - sum_w2, "c8")
                            elif S[s][i-1][1] != 0:
                                sum_w2 += quicksum(y_vars[s+1,l,2,i] for l in L)
                                model.addCons(w_vars[s+1,i] <= (S[s][i-1][0]+S[s][i-1][1]) - sum_w2, "c8")
                            
                            
                    # Restricción 10: w (partial late)
                    
                    for i in I:
                        sum_w2 = Expr()
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            if S[s][i-1][0] != 0:
                                sum_w2 += quicksum(y_vars[s+1,l,1,i] + y_vars[s+1,l,2,i] for l in L)
                                model.addCons(w_vars[s+1,i] <= sum_w2, "c9")
                            elif S[s][i-1][1] != 0:
                                sum_w2 += quicksum(y_vars[s+1,l,2,i] for l in L)
                                model.addCons(w_vars[s+1,i] <= sum_w2, "c9")


                    # Restricción 11: gamma (null)
                    
                    for i in I:
                        sum_gamma = Expr()
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            if S[s][i-1][0] != 0:
                                sum_gamma += quicksum(y_vars[s+1,l,1,i] + y_vars[s+1,l,2,i] for l in L)
                            if S[s][i-1][1] != 0:
                                sum_gamma += quicksum(y_vars[s+1,l,2,i] for l in L)
                            model.addCons(sum_gamma + gamma_vars[s+1,i] >= 1, "c_11")
                            
#                    Restricción 12: only one variable per demand point
                    for i in I:
                        if S[s][i-1][0] + S[s][i-1][1] > 0:
                            model.addCons(f_vars[s+1,i] + g_vars[s+1,i] + h_vars[s+1,i] + w_vars[s+1,i] + gamma_vars[s+1,i] <= 1, "c_12")
                    
                    
       
    
                # Optimize model
                model.optimize()

