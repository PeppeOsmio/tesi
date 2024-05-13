# Statistics for AEA 70/71 Cone Penetrometer Data
# April 27, 2022 ##
# Updated July 10, 2022 #

# Comparisons of interest#
#   Stover levels within CP (0, 35, and 60% stover harvest)
#   Factorial comparison: Medium and High stover removal x NT/CP
#   Treatment 6 vs Treatment 9

# Load libraries ####
library(dplyr)
library(tidyr)
library(ggplot2)
library(readxl)
library(RColorBrewer)
library(hrbrthemes)
library(viridis)
library(forcats)
library(nlme)

# Load data for cone index, bulk density, and water content ####
# Set file path (FP)
FP <-c("C:/Users/claire.phillips/Box/Group Projects/Penetrometer/AEA 7071 Tillage Trial/Database Submission/")
CI.df<-read.csv(paste(FP,"Field 70-71 ConeIndex_BulkDensityDepths_2021.csv", sep=""))
dim(CI.df);names(CI.df)

# [1] 384  20
# [1] "Profile"        "Depth.Upper"    "Wheel"          "Rep"           
# [5] "Depth.Lower"    "ConeIndex"      "Crop"           "Tillage"       
# [9] "ResidueRemoved" "Plot"           "Field"          "Block"         
# [13] "Plot_2"         "Side"           "Tx"             "GWC"           
# [17] "BD"             "VWC"            "TC.perc"        "OM.perc"    

CI.df <- mutate(CI.df,
                  Depth = as.factor(paste(as.character(Depth.Upper),as.character(Depth.Lower), sep="-")),
                  Plot=as.factor(Plot),
                  Side=as.factor(Side),
                  Field=as.factor(Field),
                  Block=as.factor(Block),
                  Plot_2=as.factor(Plot_2),
                  Wheel=as.factor(Wheel),
                  Crop=as.factor(Crop),
                  Tillage=as.factor(Tillage),
                  ResidueRemoved=as.factor(ResidueRemoved),
                  VWC = GWC * BD,
                  Tx = as.factor(Tx))
CI.df$Depth <- factor(CI.df$Depth, levels=c('0-5',"5-15","15-30","30-60"))

# Plot data to check for normality, etc ####
CP_CC_Only<-filter(CI.df,Tillage=="CP", Crop=="CC")
ggplot(CP_CC_Only, aes(x=Wheel, y=ConeIndex, fill=Depth)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Residue Removal Impacts for Chisel Plow") +
  ylab("Cone Index (MPa)") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(cols=vars(ResidueRemoved), rows=vars(Depth),
             labeller = labeller(.cols = label_both)) +
  theme_bw(base_size=16)

#Organize differently to highlight significant results
ggplot(CP_CC_Only, aes(x=ResidueRemoved, y=ConeIndex, fill=Depth)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Residue Removal Impacts Under Chisel Plow Tillage") +
  ylab("Cone Index (MPa)") +
  xlab("Residue Removed (%)") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(cols=vars(Wheel), rows=vars(Depth)) +
  theme_bw(base_size=16)
 
# Plot Cone Index aggregated by depth as profiles for Chisel Plow, Figure 4 ####
CP_CC_Summary <- CP_CC_Only %>%
  mutate(Depth.Midpoint = (Depth.Upper + Depth.Lower)/2) %>%
  group_by(Tillage, Wheel, ResidueRemoved, Depth.Midpoint) %>%
  summarise(CI.mean = mean(ConeIndex, na.rm = TRUE),
            CI.sd = sd(ConeIndex, na.rm = TRUE),
            BD.mean = mean(BD),
            BD.sd = sd(BD),
            GWC.mean = mean(GWC),
            GWC.sd = sd(GWC),
            VWC.mean = mean (VWC),
            VWC.sd = sd(VWC),
            TC.mean = mean(TC.perc),
            TC.sd = sd(TC.perc))

# Offset Depth for Trafficked vs Untrafficked
CP_CC_Summary$Plot.Depth <- CP_CC_Summary$Depth.Midpoint
CP_CC_Summary[CP_CC_Summary$Wheel=="Untrafficked",'Plot.Depth'] <- CP_CC_Summary[CP_CC_Summary$Wheel=="Untrafficked",'Depth.Midpoint'] + 0.4
# Annotate<-data.frame(x=rep(c(1.5,9,21.5,47),each=6),y=rep(c(0.6,1,1.6,1.6), each=6), 
#                      text=c("N.S.","p = 0.04","p = 0.04",
#                             "p = 0.01", "N.S.", "p = 0.0004",
#                             "N.S.", "p = 0.04", "p = 0.04",
#                             "p = 0.05", "p = 0.05", "p = 0.003", rep(NA,12)))

# Specify location to put Figures
FigureFP <- c("C:/Users/claire.phillips/Box/Group Projects/Penetrometer/AEA 7071 Tillage Trial/Penetration Resistance Manuscript/Figures/")

ggplot(CP_CC_Summary, aes(x=Plot.Depth, y=CI.mean, pch=Wheel,col=ResidueRemoved)) +
  scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                "60" = "steelblue"), guide="none") +
  geom_point(size=4) +
  geom_linerange(aes(ymin= CI.mean - CI.sd, ymax = CI.mean + CI.sd)) +
  geom_line() +
  xlim(50,0) +
  ylim(-0.1,2.1) +
  ylab("Penetration Resistance (MPa)") +
  xlab("Depth, Midpoint (cm)") +
  theme_classic() +
  coord_flip() +
  facet_grid(~ResidueRemoved) +
  theme(text = element_text(size = 17),
        axis.ticks.length=unit(-0.25, "cm")) 
ggsave(paste(FigureFP,"CP_CC_ConeIndex_byCoreDepths.jpg",sep=""),
       width=10.5, height = 5, units = "in") 

# Plot BD, WC, and perc C profiles for chisel plow ####

# Plot BD in the same way, CHISEL PLOW
CP_CC_Summary$Plot.Depth <- CP_CC_Summary$Depth.Midpoint
CP_CC_Summary[CP_CC_Summary$ResidueRemoved==35,'Plot.Depth'] <- CP_CC_Summary[CP_CC_Summary$ResidueRemoved==35,'Depth.Midpoint'] + 0.4
CP_CC_Summary[CP_CC_Summary$ResidueRemoved==60,'Plot.Depth'] <- CP_CC_Summary[CP_CC_Summary$ResidueRemoved==60,'Depth.Midpoint'] + 0.8

CP_CC_Untrafficked <- filter(CP_CC_Summary, Wheel=="Untrafficked")

ggplot(CP_CC_Untrafficked, aes(x=Plot.Depth, y=BD.mean, color=ResidueRemoved, shape=ResidueRemoved)) +
  scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                "60" = "steelblue")) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= BD.mean - BD.sd, ymax = BD.mean + BD.sd)) +
  geom_line(aes(y=BD.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  #geom_line() +
  xlim(50,0) +
  ylim(1.0,2.0)+
  ylab(expression(Bulk~Density~group("(",g~cm^{-3},")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = c(0.3, 0.2)) +
  labs(color = "Stover\nRemoved (%)", shape = "Stover\nRemoved (%)")
ggsave(paste(FigureFP,"CP_CC_BulkDensity.jpg", sep=""),
       width=4, height = 5, units = "in") 

# Plot GWC in the same way, CHISEL PLOW
ggplot(CP_CC_Untrafficked, aes(x=Plot.Depth, y=GWC.mean, color=ResidueRemoved, shape=ResidueRemoved)) +
  scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                "60" = "steelblue")) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= GWC.mean - GWC.sd, ymax = GWC.mean + GWC.sd)) +
  geom_line(aes(y=GWC.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  xlim(50,0) +
  ylim(0.15,0.3)+
  ylab(expression(Soil~Water~Content~group("(",g~g^{-1},")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = "none") 
ggsave(paste(FigureFP,"CP_CC_GWC.jpg",sep=""),
       width=4, height = 5, units = "in") 

# Plot VWC in the same way, CHISEL PLOW
# Note that VWC takes on the profile pattern of BD
ggplot(CP_CC_Untrafficked, aes(x=Plot.Depth, y=VWC.mean, color=ResidueRemoved, shape=ResidueRemoved)) +
  scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                "60" = "steelblue")) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= VWC.mean - VWC.sd, ymax = VWC.mean + VWC.sd)) +
  geom_line(aes(y=VWC.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  xlim(50,0) +
  ylab(expression(Soil~Water~Content~group("(",g~cm^{-3},")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = "none") 
ggsave(paste(FigureFP,"CP_CC_VWC.jpg",sep=""),
       width=4, height = 5, units = "in") 

# Plot Perc TC in the same way, CHISEL PLOW
ggplot(CP_CC_Untrafficked, aes(x=Plot.Depth, y=TC.mean, color=ResidueRemoved, shape=ResidueRemoved)) +
  scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                "60" = "steelblue")) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= TC.mean - TC.sd, ymax = TC.mean + TC.sd)) +
  geom_line(aes(y=TC.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  xlim(50,0) +
  ylim(0.5,3)+
  ylab(expression("Organic C (%)")) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = "none")
ggsave(paste(FigureFP,"CP_CC_TC.jpg",sep=""),
       width=4, height = 5, units = "in") 

# Plot PR in untrafficked areas in same way
CI_Untrafficked_CP_CC_Summary <- CP_CC_Only %>%
  filter(Wheel=="Untrafficked") %>%
  mutate(Plot.Depth = (Depth.Upper + Depth.Lower)/2) %>%
  group_by(Tillage, Wheel, ResidueRemoved, Plot.Depth) %>%
  summarise(CI.mean = mean(ConeIndex, na.rm = TRUE),
            CI.sd = sd(ConeIndex, na.rm = TRUE))

CI_Untrafficked_CP_CC_Summary[CI_Untrafficked_CP_CC_Summary$ResidueRemoved==35,'Plot.Depth'] <- CI_Untrafficked_CP_CC_Summary[CI_Untrafficked_CP_CC_Summary$ResidueRemoved==35,'Plot.Depth'] + 0.4
CI_Untrafficked_CP_CC_Summary[CI_Untrafficked_CP_CC_Summary$ResidueRemoved==60,'Plot.Depth'] <- CI_Untrafficked_CP_CC_Summary[CI_Untrafficked_CP_CC_Summary$ResidueRemoved==60,'Plot.Depth'] + 0.8

ggplot(CI_Untrafficked_CP_CC_Summary , aes(x=Plot.Depth, y=CI.mean, color=ResidueRemoved, shape=ResidueRemoved)) +
  scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                "60" = "steelblue")) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= CI.mean - CI.sd, ymax = CI.mean + CI.sd)) +
  geom_line(aes(y=CI.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  xlim(50,0) +
  ylim(-0.1,2.1) +
  ylab(expression(Penetration~Resistance~group("(",MPa,")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = "none") +
  labs(color = "Stover\nRemoved (%)", shape = "Stover\nRemoved (%)")
ggsave(paste(FigureFP,"CP_CC_PR_Untrafficked.jpg",sep=""),
       width=4, height = 5, units = "in") 



# plot BD and soil moisture as box plots in facet plot
ggplot(CP_CC_Only, aes(x=ResidueRemoved, y=BD, fill=Depth)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Residue Removal Impacts for Chisel Plow") +
  ylab("Bulk Density (g/cm3)") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(rows=vars(Depth)) +
  theme_bw(base_size=16)

ggplot(CP_CC_Only, aes(x=ResidueRemoved, y=GWC, fill=Depth)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Residue Removal Impacts for Chisel Plow") +
  ylab("Water content (g/g)") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(rows=vars(Depth)) +
  theme_bw(base_size=16)



# Plot CI vs BD and WC as regressions for chisel plow ####
# Plot CI vs GWC as regression
ggplot(CP_CC_Only, aes(y=ConeIndex, x=GWC)) +
  geom_point(aes(color=Depth)) +
  ggtitle("Continuous Corn, Chisel Plow") +
  #geom_smooth(aes(color=Depth),method="lm") +
  geom_smooth(method="lm", color="black") +
  ylab("Cone Index (MPa)") +
  xlab(expression(Soil~Water~Content~group("(",g~g^{-1},")"))) +
  theme_classic(base_size=16) 
ggsave(paste(FigureFP,"CP_CC_CIvsGWC_v2.jpg",sep=""),
       width=6, height = 5, units = "in") 

summary(lm(ConeIndex~GWC, data=CP_CC_Only))

# Plot CI vs BD as regression
ggplot(CP_CC_Only, aes(y=ConeIndex, x=BD)) +
  geom_point(aes(color=Depth)) +
  ggtitle("Continuous Corn, Chisel Plow") +
  #geom_smooth(color=Depth),method="lm") +
  geom_smooth(method="lm", color="black") +
  ylab("Cone Index (MPa)") +
  xlab("Bulk Density (g/cm3)") +
  theme_classic(base_size=16)
ggsave(paste(FigureFP,"CP_CC_CIvsBD_v2.jpg",sep=""),
       width=6, height = 5, units = "in") 



# Plot CI vs VWC as regression
ggplot(CP_CC_Only, aes(y=ConeIndex, x=VWC)) +
  geom_point(aes(color=Depth)) +
  ggtitle("Continuous Corn, Chisel Plow") +
  geom_smooth(method="lm") +
  ylab("Cone Index (MPa)") +
  xlab(expression(Volumetric~Water~Content~group("(",g~cm^{-3},")"))) +
  theme_classic(base_size=16)




# Check out and run agriTutorial for split-plot design code ####
  library(agriTutorial)
  example("example1")

  require(lmerTest)
  require(emmeans)
  require(pbkrtest)
  options(contrasts = c('contr.treatment', 'contr.poly'))

# Analyze Traffic and Residue Removal Impacts on Cone Index for Chisel Plow plots ####
  
  # Make tibbles for each depth
  CP_CC_0to5<-filter(CI.df,Depth.Lower == '5' & Tillage == 'CP' & Crop == 'CC')
  dim(CP_CC_0to5)

  CP_CC_5to15<-filter(CI.df,Depth.Lower == '15' & Tillage == 'CP' & Crop == 'CC')
  dim(CP_CC_5to15)
  
  CP_CC_15to30<-filter(CI.df,Depth.Lower == '30' & Tillage == 'CP' & Crop == 'CC')
  dim(CP_CC_15to30)
  
  CP_CC_30to60<-filter(CI.df,Depth.Lower == '60' & Tillage == 'CP' & Crop == 'CC')
  dim(CP_CC_30to60)
  
  #ANOVA Tables
  CI_0to5.aov1 = aov(ConeIndex ~ Block + Wheel * ResidueRemoved +
                       Error(Block/Plot_2),CP_CC_0to5)
  summary(CI_0to5.aov1 , df = "Kenward-Roger", type = 1)
  
  CI_5to15.aov1 = aov(ConeIndex ~ Block + Wheel * ResidueRemoved +
                        Error(Block/Plot_2),CP_CC_5to15)
  summary(CI_5to15.aov1 , df = "Kenward-Roger", type = 1)
  
  CI_15to30.aov1 = aov(ConeIndex ~ Block + Wheel * ResidueRemoved +
                         Error(Block/Plot_2),CP_CC_15to30)
  summary(CI_15to30.aov1 , df = "Kenward-Roger", type = 1)
  
  CI_30to60.aov1 = aov(ConeIndex ~ Block + Wheel * ResidueRemoved +
                         Error(Block/Plot_2),CP_CC_30to60)
  summary(CI_30to60.aov1 , df = "Kenward-Roger", type = 1)


  #Means and SEs
  CI_0to5.means = lmer(ConeIndex ~ Block + Wheel * ResidueRemoved + (1|Block:Plot_2), data=CP_CC_0to5)
  anova(CI_0to5.means, df = "Kenward-Roger", type = 1)
  plot(CI_0to5.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 0-5 cm")
  emmeans::emmeans(CI_0to5.means, ~ResidueRemoved)
  emmeans::emmeans(CI_0to5.means, ~Wheel)
  emmeans::emmeans(CI_0to5.means, ~ResidueRemoved * Wheel)
  
  CI_5to15.means = lmer(ConeIndex ~ Block + Wheel * ResidueRemoved + (1|Block:Plot_2), data=CP_CC_5to15)
  anova(CI_5to15.means, df = "Kenward-Roger", type = 1)
  plot(CI_5to15.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 0-5 cm")
  (emmeans::emmeans(CI_5to15.means, ~ResidueRemoved))
  (emmeans::emmeans(CI_5to15.means, ~Wheel))
  (emmeans::emmeans(CI_5to15.means, ~ResidueRemoved * Wheel))
  
  CI_15to30.means = lmer(ConeIndex ~ Block + Wheel * ResidueRemoved + (1|Block:Plot_2), data=CP_CC_15to30)
  anova(CI_15to30.means, df = "Kenward-Roger", type = 1)
  plot(CI_15to30.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 0-5 cm")
  emmeans::emmeans(CI_15to30.means, ~ResidueRemoved)
  emmeans::emmeans(CI_15to30.means, ~Wheel)
  emmeans::emmeans(CI_15to30.means, ~ResidueRemoved * Wheel)
  
  CI_30to60.means = lmer(ConeIndex ~ Block + Wheel * ResidueRemoved + (1|Block:Plot_2), data=CP_CC_30to60)
  anova(CI_30to60.means, df = "Kenward-Roger", type = 1)
  plot(CI_30to60.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 0-5 cm")
  emmeans::emmeans(CI_30to60.means, ~ResidueRemoved)
  emmeans::emmeans(CI_30to60.means, ~Wheel)
  emmeans::emmeans(CI_30to60.means, ~ResidueRemoved * Wheel)
  
  # Analyze residue removal as numeric
  CP_CC_0to5_v2 <- mutate(CP_CC_0to5, ResidueRemoved = as.numeric(as.character(ResidueRemoved)))
  CP_CC_5to15_v2 <- mutate(CP_CC_5to15, ResidueRemoved = as.numeric(as.character(ResidueRemoved)))
  CP_CC_15to30_v2 <- mutate(CP_CC_15to30, ResidueRemoved = as.numeric(as.character(ResidueRemoved)))
  CI_0to5.lmer = lmer(ConeIndex ~ Block + Wheel * ResidueRemoved + (1|Block:Plot_2), data=CP_CC_0to5_v2)
  summary(CI_0to5.lmer)
  
  CI_5to15.lmer = lmer(ConeIndex ~ Block + Wheel * ResidueRemoved + (1|Block:Plot_2), data=CP_CC_5to15_v2)
  summary(CI_5to15.lmer)
  
  CI_15to30.lmer = lmer(ConeIndex ~ Block + Wheel * ResidueRemoved + (1|Block:Plot_2), data=CP_CC_15to30_v2)
  summary(CI_15to30.lmer)
  
  
  #REML constrasts and sed's for qualitative residue removal effects and traffic
  w.r.0to5 = emmeans::emmeans(CI_0to5.means, ~Wheel|ResidueRemoved)
  emmeans::contrast(w.r.0to5, alpha = 0.05, method = "pairwise")
  r.w.0to5 = emmeans::emmeans(CI_0to5.means, ~ResidueRemoved|Wheel)
  emmeans::contrast(r.w.0to5, alpha = 0.05, method = "pairwise")
  
  w.r.5to15 = emmeans::emmeans(CI_5to15.means, ~Wheel|ResidueRemoved)
  emmeans::contrast(w.r.5to15, alpha = 0.05, method = "pairwise")
  r.w.5to15 = emmeans::emmeans(CI_5to15.means, ~ResidueRemoved|Wheel)
  emmeans::contrast(r.w.5to15, alpha = 0.05, method = "pairwise")
  
  w.r.15to30 = emmeans::emmeans(CI_15to30.means, ~Wheel|ResidueRemoved)
  emmeans::contrast(w.r.15to30, alpha = 0.05, method = "pairwise")
  r.w.15to30 = emmeans::emmeans(CI_15to30.means, ~ResidueRemoved|Wheel)
  emmeans::contrast(r.w.15to30, alpha = 0.05, method = "pairwise")
  
  w.r.30to60 = emmeans::emmeans(CI_30to60.means, ~Wheel|ResidueRemoved)
  emmeans::contrast(w.r.30to60, alpha = 0.05, method = "pairwise")
  r.w.30to60 = emmeans::emmeans(CI_30to60.means, ~ResidueRemoved|Wheel)
  emmeans::contrast(r.w.30to60, alpha = 0.05, method = "pairwise")
  
# Compare Tx 1 (CP0) and Tx 6 (NT60) ####
  CC_0to5<-filter(CI.df,Depth.Lower == '5' & Crop == 'CC')
  dim(CC_0to5)
  
  CI_0to5.means = lmer(ConeIndex ~ Block + Wheel * Tx + (1|Block:Plot_2), data=CC_0to5)
  anova(CI_0to5.means, df = "Kenward-Roger", type = 1)
  plot(CI_0to5.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 0-5 cm")
  Tx.0to5 = emmeans::emmeans(CI_0to5.means, ~Tx)
  emmeans::contrast(Tx.0to5, alpha = 0.05, method = "pairwise")
  Tx.w.0to5 = emmeans(CI_0to5.means, ~Wheel|Tx)
  emmeans::contrast(Tx.w.0to5,alpha = 0.05, method = "pairwise")
  w.Tx.0to5 = emmeans(CI_0to5.means, ~Tx|Wheel)
  emmeans::contrast(w.Tx.0to5,alpha = 0.05, method = "pairwise")
  
  CC_5to15<-filter(CI.df,Depth.Lower == '15' & Crop == 'CC')
  dim(CC_5to15)
  
  CI_5to15.means = lmer(ConeIndex ~ Block + Wheel * Tx + (1|Block:Plot_2), data=CC_5to15)
  anova(CI_5to15.means, df = "Kenward-Roger", type = 1)
  plot(CI_5to15.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 5-15 cm")
  (Tx.5to15 = emmeans::emmeans(CI_5to15.means, ~Tx))
  emmeans::contrast(Tx.5to15, alpha = 0.05, method = "pairwise")
  Tx.w.5to15 = emmeans(CI_5to15.means, ~Wheel|Tx)
  emmeans::contrast(Tx.w.5to15,alpha = 0.05, method = "pairwise")
  w.Tx.5to15 = emmeans(CI_5to15.means, ~Tx|Wheel)
  emmeans::contrast(w.Tx.5to15,alpha = 0.05, method = "pairwise")
  
  CC_15to30<-filter(CI.df,Depth.Lower == '30' & Crop == 'CC')
  dim(CC_15to30)
  
  CI_15to30.means = lmer(ConeIndex ~ Block + Wheel * Tx + (1|Block:Plot_2), data=CC_15to30)
  anova(CI_15to30.means, df = "Kenward-Roger", type = 1)
  plot(CI_15to30.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 15-30 cm")
  (Tx.15to30 = emmeans::emmeans(CI_15to30.means, ~Tx))
  emmeans::contrast(Tx.15to30, alpha = 0.05, method = "pairwise")
  Tx.w.15to30 = emmeans(CI_15to30.means, ~Wheel|Tx)
  emmeans::contrast(Tx.w.15to30,alpha = 0.05, method = "pairwise")
  (w.Tx.15to30 = emmeans(CI_15to30.means, ~Tx|Wheel))
  emmeans::contrast(w.Tx.15to30,alpha = 0.05, method = "pairwise")
  
  CC_30to60<-filter(CI.df,Depth.Lower == '60' & Crop == 'CC')
  dim(CC_30to60)
  
  CI_30to60.means = lmer(ConeIndex ~ Block + Wheel * Tx + (1|Block:Plot_2), data=CC_30to60)
  anova(CI_30to60.means, df = "Kenward-Roger", type = 1)
  plot(CI_30to60.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 30-60 cm")
  (Tx.30to60 = emmeans::emmeans(CI_30to60.means, ~Tx))
  emmeans::contrast(Tx.30to60, alpha = 0.05, method = "pairwise")
  Tx.w.30to60 = emmeans(CI_30to60.means, ~Wheel|Tx)
  emmeans::contrast(Tx.w.30to60,alpha = 0.05, method = "pairwise")
  (w.Tx.30to60 = emmeans(CI_30to60.means, ~Tx|Wheel))
  emmeans::contrast(w.Tx.30to60,alpha = 0.05, method = "pairwise")
  
  # Compare TC in Tx1 and Tx6
  CI_0to5.means = lm(TC.perc ~ Block * Tx, data=CC_0to5)
  anova(CI_0to5.means)
  (Tx.0to5 = emmeans::emmeans(CI_0to5.means, ~Tx))
  emmeans::contrast(Tx.0to5,alpha = 0.05, method = "pairwise")
 
  CI_5to15.means = lm(TC.perc ~ Block * Tx, data=CC_5to15)
  anova(CI_5to15.means)
  (Tx.5to15 = emmeans::emmeans(CI_5to15.means, ~Tx))
  emmeans::contrast(Tx.5to15,alpha = 0.05, method = "pairwise")
  
  CI_15to30.means = lm(TC.perc ~ Block * Tx, data=CC_15to30)
  anova(CI_15to30.means)
  (Tx.15to30 = emmeans::emmeans(CI_15to30.means, ~Tx))
  emmeans::contrast(Tx.15to30,alpha = 0.05, method = "pairwise")
  
  CI_30to60.means = lm(TC.perc ~ Block * Tx, data=CC_30to60)
  anova(CI_30to60.means)
  (Tx.30to60 = emmeans::emmeans(CI_30to60.means, ~Tx))
  emmeans::contrast(Tx.30to60,alpha = 0.05, method = "pairwise")
  
  # Compare BD in Tx1 and Tx6
  CI_0to5.means = lm(BD ~ Block * Tx, data=CC_0to5)
  anova(CI_0to5.means)
  (Tx.0to5 = emmeans::emmeans(CI_0to5.means, ~Tx))
  emmeans::contrast(Tx.0to5,alpha = 0.05, method = "pairwise")
  
  CI_5to15.means = lm(BD ~ Block * Tx, data=CC_5to15)
  anova(CI_5to15.means)
  (Tx.5to15 = emmeans::emmeans(CI_5to15.means, ~Tx))
  emmeans::contrast(Tx.5to15,alpha = 0.05, method = "pairwise")
  
  CI_15to30.means = lm(BD ~ Block * Tx, data=CC_15to30)
  anova(CI_15to30.means)
  (Tx.15to30 = emmeans::emmeans(CI_15to30.means, ~Tx))
  emmeans::contrast(Tx.15to30,alpha = 0.05, method = "pairwise")
  
  CI_30to60.means = lm(BD ~ Block * Tx, data=CC_30to60)
  anova(CI_30to60.means)
  (Tx.30to60 = emmeans::emmeans(CI_30to60.means, ~Tx))
  emmeans::contrast(Tx.30to60,alpha = 0.05, method = "pairwise")
  
  
  
# Analyze Residue removal impacts on bulk density, GWC, and SOC for Chisel plow plots ####
  BD_0to5.aov1 = aov(BD ~ Block + ResidueRemoved +
                       Error(Block/Plot_2),CP_CC_0to5)
  summary(BD_0to5.aov1 , df = "Kenward-Roger", type = 1)
  
  BD_5to15.aov1 = aov(BD ~ Block + ResidueRemoved +
                        Error(Block/Plot_2),CP_CC_5to15)
  summary(BD_5to15.aov1 , df = "Kenward-Roger", type = 1)
  
  BD_15to30.aov1 = aov(BD ~ Block + ResidueRemoved +
                         Error(Block/Plot_2),CP_CC_15to30)
  summary(BD_15to30.aov1 , df = "Kenward-Roger", type = 1)
  
  BD_30to60.aov1 = aov(BD ~ Block + ResidueRemoved +
                         Error(Block/Plot_2),CP_CC_30to60)
  summary(BD_30to60.aov1 , df = "Kenward-Roger", type = 1)
  
  #Evaluate GWC 
  GWC_0to5.aov1 = aov(GWC ~ Block + ResidueRemoved +
                        Error(Block/Plot_2),CP_CC_0to5)
  summary(GWC_0to5.aov1 , df = "Kenward-Roger", type = 1)
  
  GWC_5to15.aov1 = aov(GWC ~ Block + ResidueRemoved +
                         Error(Block/Plot_2),CP_CC_5to15)
  summary(GWC_5to15.aov1 , df = "Kenward-Roger", type = 1)
  
  GWC_15to30.aov1 = aov(GWC ~ Block + ResidueRemoved +
                          Error(Block/Plot_2),CP_CC_15to30)
  summary(GWC_15to30.aov1 , df = "Kenward-Roger", type = 1)
  
  GWC_30to60.aov1 = aov(GWC ~ Block + ResidueRemoved +
                          Error(Block/Plot_2),CP_CC_30to60)
  summary(GWC_30to60.aov1 , df = "Kenward-Roger", type = 1)
  
  #Evaluate SOC 
  TC_0to5.aov1 = aov(TC.perc ~ Block + ResidueRemoved,CP_CC_0to5)
  summary(TC_0to5.aov1)
  
  TC_5to15.aov1 = aov(TC.perc ~ Block + ResidueRemoved, CP_CC_5to15)
  summary(TC_5to15.aov1)
  
  TC_15to30.aov1 = aov(TC.perc ~ Block + ResidueRemoved,CP_CC_15to30)
  summary(TC_15to30.aov1)
  
  TC_30to60.aov1 = aov(TC.perc ~ Block + ResidueRemoved, CP_CC_30to60)
  summary(TC_30to60.aov1)
  

# Evaluate trafficed - untrafficked for each location
CI_byWheel<-pivot_wider(CI.df,names_from="Wheel",values_from="ConeIndex")
CI_byWheel$Difference = CI_byWheel$Trafficked - CI_byWheel$Untrafficked

ggplot(CI_byWheel, aes(x=ResidueRemoved, y=Difference, fill=Depth.Lower)) +
  geom_boxplot(show.legend=FALSE) +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.2,show.legend=FALSE) +
  facet_grid(rows=vars(Depth.Lower))+
  theme_ipsum_pub()

Top_byWheel<-filter(CI_byWheel,Depth.Lower == '150')
dim(Top_byWheel)

Mid_byWheel<-filter(CI_byWheel,Depth.Lower == '300')
dim(Mid_byWheel)

Bottom_byWheel<-filter(CI_byWheel,Depth.Lower == '600')
dim(Bottom_byWheel)

Top_byWheel.means = lmer(Difference ~ Block + ResidueRemoved + (1|Block:Plot_2), data=Top_byWheel)
anova(Top_byWheel.means, df = "Kenward-Roger", type = 1)

Mid_byWheel.means = lmer(Difference ~ Block + ResidueRemoved + (1|Block:Plot_2), data=Mid_byWheel)
anova(Mid_byWheel.means, df = "Kenward-Roger", type = 1)

Bottom_byWheel.means = lmer(Difference ~ Block + ResidueRemoved + (1|Block:Plot_2), data=Bottom_byWheel)
anova(Bottom_byWheel.means, df = "Kenward-Roger", type = 1)

r.Bottom = emmeans::emmeans(Bottom_byWheel.means, ~ResidueRemoved)
emmeans::contrast(r.Bottom, alpha = 0.05, method = "pairwise")

# Adding pairwise comparisons to plots:
#https://rpkgs.datanovia.com/ggpubr/reference/stat_compare_means.html

# Analyze Traffic and Residue Removal Impacts on Cone Index for No-till Plots ####
NT_CC_Only<-CI.df[CI.df$Tillage=="NT" & CI.df$Crop=="CC",]
ggplot(NT_CC_Only, aes(x=Wheel, y=ConeIndex, fill=Depth)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Residue Removal Impacts for No-till") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(cols=vars(ResidueRemoved), rows=vars(Depth)) +
  theme_bw(base_size=16)

NT_CC_0to5<-filter(CI.df,Tillage== 'NT', Crop == 'CC', Depth == '0-5')
dim(NT_CC_0to5)

NT_CC_5to15<-filter(CI.df,Tillage== 'NT', Crop == 'CC', Depth == '5-15')
dim(NT_CC_5to15)

NT_CC_15to30<-filter(CI.df,Tillage== 'NT', Crop == 'CC', Depth == '15-30')
dim(NT_CC_15to30)

NT_CC_30to60<-filter(CI.df,Tillage== 'NT', Crop == 'CC', Depth == '30-60')
dim(NT_CC_30to60)

NT_CC_0to5.aov = aov(ConeIndex ~ Block + Wheel * ResidueRemoved + Error(Block/Plot_2),NT_CC_0to5)
summary(NT_CC_0to5.aov, df = "Kenward-Roger", type = 1)

NT_CC_5to15.aov = aov(ConeIndex ~ Block + Wheel * ResidueRemoved + Error(Block/Plot_2),NT_CC_5to15)
summary(NT_CC_5to15.aov, df = "Kenward-Roger", type = 1)

NT_CC_15to30.aov = aov(ConeIndex ~ Block + Wheel * ResidueRemoved + Error(Block/Plot_2),NT_CC_15to30)
summary(NT_CC_15to30.aov, df = "Kenward-Roger", type = 1)

NT_CC_30to60.aov = aov(ConeIndex ~ Block + Wheel * ResidueRemoved + Error(Block/Plot_2),NT_CC_30to60)
summary(NT_CC_30to60.aov, df = "Kenward-Roger", type = 1)

# No post-hoc tests required for most because main factors were N.S.
# Only 0-5 cm had wheel effect (p=0.0529)
CI_0to5_NT.means = lmer(ConeIndex ~ Block + Wheel * ResidueRemoved + (1|Block:Plot_2), data=NT_CC_0to5)
anova(CI_0to5_NT.means, df = "Kenward-Roger", type = 1)
plot(CI_0to5_NT.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "Full analysis 0-5 cm")
emmeans::emmeans(CI_0to5_NT.means, ~ResidueRemoved)
(WheelMeans<-emmeans::emmeans(CI_0to5_NT.means, ~Wheel))
emmeans::emmeans(CI_0to5_NT.means, ~ResidueRemoved * Wheel)

#REML constrasts and sed's for qualitative residue removal effects and traffic
emmeans::contrast(WheelMeans, alpha = 0.05, method = "pairwise")
w.r.0to5.NT = emmeans::emmeans(CI_0to5_NT.means, ~Wheel|ResidueRemoved)
emmeans::contrast(w.r.0to5.NT, alpha = 0.05, method = "pairwise")
r.w.0to5.NT = emmeans::emmeans(CI_0to5_NT.means, ~ResidueRemoved|Wheel)
emmeans::contrast(r.w.0to5.NT, alpha = 0.05, method = "pairwise")

# Analyze residue removal impacts on bulk density and GWC for no-till plots ####
# Note that they also get analyzed with tillage included in the model, below.
# This is to mirror the analysis for chisel plow plots, which includes 0% residue removal
BD_0to5_NT.aov1 = aov(BD ~ Block + ResidueRemoved, NT_CC_0to5)
summary(BD_0to5_NT.aov1 , df = "Kenward-Roger", type = 1)

BD_5to15_NT.aov1 = aov(BD ~ Block + ResidueRemoved,NT_CC_5to15)
summary(BD_5to15_NT.aov1 , df = "Kenward-Roger", type = 1)

BD_15to30_NT.aov1 = aov(BD ~ Block + ResidueRemoved, NT_CC_15to30)
summary(BD_15to30_NT.aov1 , df = "Kenward-Roger", type = 1)

BD_30to60_NT.aov1 = aov(BD ~ Block + ResidueRemoved,NT_CC_30to60)
summary(BD_30to60_NT.aov1 , df = "Kenward-Roger", type = 1)

#Evaluate GWC 
GWC_0to5_NT.aov1 = aov(GWC ~ Block + ResidueRemoved, NT_CC_0to5)
summary(GWC_0to5_NT.aov1 , df = "Kenward-Roger", type = 1)

GWC_5to15_NT.aov1 = aov(GWC ~ Block + ResidueRemoved, NT_CC_5to15)
summary(GWC_5to15_NT.aov1 , df = "Kenward-Roger", type = 1)

GWC_15to30_NT.aov1 = aov(GWC ~ Block + ResidueRemoved, NT_CC_15to30)
summary(GWC_15to30_NT.aov1 , df = "Kenward-Roger", type = 1)

GWC_30to60_NT.aov1 = aov(GWC ~ Block + ResidueRemoved, NT_CC_30to60)
summary(GWC_30to60_NT.aov1 , df = "Kenward-Roger", type = 1)

#Evaluate SOC 
TC_0to5.aov1 = aov(TC.perc ~ Block + ResidueRemoved,NT_CC_0to5)
summary(TC_0to5.aov1)

TC_5to15.aov1 = aov(TC.perc ~ Block + ResidueRemoved, NT_CC_5to15)
summary(TC_5to15.aov1)

TC_15to30.aov1 = aov(TC.perc ~ Block + ResidueRemoved,NT_CC_15to30)
summary(TC_15to30.aov1)

TC_30to60.aov1 = aov(TC.perc ~ Block + ResidueRemoved, NT_CC_30to60)
summary(TC_30to60.aov1)

# Make NT profile plots, Figure 4 ####
NT_CC_Summary <- NT_CC_Only %>%
  mutate(Depth.Midpoint = (Depth.Upper + Depth.Lower)/2) %>%
  group_by(Tillage, Wheel, ResidueRemoved, Depth.Midpoint) %>%
  summarise(CI.mean = mean(ConeIndex, na.rm = TRUE),
            CI.sd = sd(ConeIndex, na.rm = TRUE),
            BD.mean = mean(BD),
            BD.sd = sd(BD),
            GWC.mean = mean(GWC),
            GWC.sd = sd(GWC),
            VWC.mean = mean (VWC),
            VWC.sd = sd(VWC),
            TC.mean = mean(TC.perc),
            TC.sd = sd(TC.perc))

# Offset Depth for Trafficked vs Untrafficked
NT_CC_Summary$Plot.Depth <- NT_CC_Summary$Depth.Midpoint
NT_CC_Summary[NT_CC_Summary$Wheel=="Untrafficked",'Plot.Depth'] <- NT_CC_Summary[NT_CC_Summary$Wheel=="Untrafficked",'Depth.Midpoint'] + 0.4

ggplot(NT_CC_Summary, aes(x=Plot.Depth, y=CI.mean, pch=Wheel,col=ResidueRemoved)) +
  scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                 "60" = "steelblue"), guide="none") +
  geom_point(size=4) +
  geom_linerange(aes(ymin= CI.mean - CI.sd, ymax = CI.mean + CI.sd)) +
  geom_line() +
  xlim(50,0) +
  ylim(-0.1,2.1) +
  ylab("Penetration Resistance (MPa)") +
  xlab("Depth, Midpoint (cm)") +
  theme_classic() +
  coord_flip() +
  facet_grid(~ResidueRemoved) +
  theme(text = element_text(size = 17),
        axis.ticks.length=unit(-0.25, "cm")) 

ggsave(paste(FigureFP,"NT_CC_ConeIndex_byCoreDepths.jpg",sep=""),
       width=7.5, height = 4.8, units = "in") 


# Plot BD in the same way, NO TILL (Fig 3)
NT_CC_Summary$Plot.Depth <- NT_CC_Summary$Depth.Midpoint
NT_CC_Summary[NT_CC_Summary$ResidueRemoved==35,'Plot.Depth'] <- NT_CC_Summary[NT_CC_Summary$ResidueRemoved==35,'Depth.Midpoint'] + 0.4
NT_CC_Summary[NT_CC_Summary$ResidueRemoved==60,'Plot.Depth'] <- NT_CC_Summary[NT_CC_Summary$ResidueRemoved==60,'Depth.Midpoint'] + 0.8

NT_CC_Untrafficked <- filter(NT_CC_Summary, Wheel=="Untrafficked")

# Get differences between till and no-till, across both levels of stover removal
# Use these symbols in figure: (* p < 0.1, ** p ??? 0.05, *** p ??? 0.01). 
BD.TillDiff <- data.frame(Plot.Depth = c(2.5), Diff = c(0.105), Signif = c("**"))

ggplot(NT_CC_Untrafficked, aes(x=Plot.Depth, y=BD.mean, shape=ResidueRemoved, color=ResidueRemoved)) +
  scale_color_manual(values = c("35" ="orange",
                                "60" = "steelblue")) +
  scale_linetype_manual(values = c("35" = "dashed",
                                "60" = "longdash")) +
  scale_shape_manual(values = c("35" = 17,
                                "60" = 15)) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= BD.mean - BD.sd, ymax = BD.mean + BD.sd)) +
  geom_line(aes(y=BD.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  # Add annotation for tillage system differences #
  annotate("segment", x = BD.TillDiff$Plot.Depth +0.4, xend = BD.TillDiff$Plot.Depth, y = 1, yend = 1 + BD.TillDiff$Diff, color = "black", size=1) +
  annotate("text", x = BD.TillDiff$Plot.Depth + 2.1, y = 1.05, label = BD.TillDiff$Signif, size = 10, color="black") +
  xlim(50,0) +
  ylim(1,2) +
  ylab(expression(Bulk~Density~group("(",g~cm^{-3},")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
      axis.ticks.length=unit(-0.25, "cm"),
      legend.position = c(0.3, 0.2)) +
labs(color = "Stover\nRemoved (%)", shape = "Stover\nRemoved (%)")
ggsave(paste(FigureFP,"NT_CC_BulkDensity.jpg",sep=""),
       width=4, height = 5, units = "in") 

# Plot GWC in the same way, NO TILL (Fig 4)
ggplot(NT_CC_Untrafficked, aes(x=Plot.Depth, y=GWC.mean, shape=ResidueRemoved, color=ResidueRemoved)) +
  scale_color_manual(values = c("35" ="orange",
                                "60" = "steelblue")) +
  scale_linetype_manual(values = c("35" = "dashed",
                                   "60" = "longdash")) +
  scale_shape_manual(values = c("35" = 17,
                                "60" = 15)) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= GWC.mean - GWC.sd, ymax = GWC.mean + GWC.sd)) +
  geom_line(aes(y=GWC.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  xlim(50,0) +
  ylim(0.15,0.3)+
  ylab(expression(Soil~Water~Content~group("(",g~g^{-1},")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = "none") 
ggsave(paste(FigureFP,"NT_CC_GWC.jpg",sep=""),
       width=4, height = 5, units = "in") 

# Plot TC in the same way, NO TILL (Fig 4)
ggplot(NT_CC_Untrafficked, aes(x=Plot.Depth, y=TC.mean, shape=ResidueRemoved, color=ResidueRemoved)) +
  scale_color_manual(values = c("35" ="orange",
                                "60" = "steelblue")) +
  scale_linetype_manual(values = c("35" = "dashed",
                                   "60" = "longdash")) +
  scale_shape_manual(values = c("35" = 17,
                                "60" = 15)) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= TC.mean - TC.sd, ymax = TC.mean + TC.sd)) +
  geom_line(aes(y=TC.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  xlim(50,0) +
  ylim(0.5,3)+
  ylab("Organic C (%)") +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = "none") 
ggsave(paste(FigureFP,"NT_CC_TC.jpg",sep=""),
       width=4, height = 5, units = "in") 

# Plot PR in untrafficked areas in same way
CI_Untrafficked_NT_CC_Summary <- NT_CC_Summary %>%
  filter(Wheel=="Untrafficked") %>%
  mutate(Plot.Depth = Depth.Midpoint) 

CI_Untrafficked_NT_CC_Summary[CI_Untrafficked_NT_CC_Summary$ResidueRemoved==35,'Plot.Depth'] <- CI_Untrafficked_NT_CC_Summary[CI_Untrafficked_NT_CC_Summary$ResidueRemoved==35,'Plot.Depth'] + 0.4
CI_Untrafficked_NT_CC_Summary[CI_Untrafficked_NT_CC_Summary$ResidueRemoved==60,'Plot.Depth'] <- CI_Untrafficked_NT_CC_Summary[CI_Untrafficked_NT_CC_Summary$ResidueRemoved==60,'Plot.Depth'] + 0.8

# Get differences between till and no-till, across both levels of stover removal
# Use these symbols to annotate the figure: (* p < 0.1, ** p ??? 0.05, *** p ??? 0.01). 
PR.Untrafficked.TillDiff <- data.frame(Plot.Depth = c(2.9, 10.4), Diff = c(0.127, 0.4116), Signif = c("*","***"))

ggplot(CI_Untrafficked_NT_CC_Summary , aes(x=Plot.Depth, y=CI.mean, color=ResidueRemoved, shape=ResidueRemoved)) +
  scale_color_manual(values = c("35" ="orange",
                                "60" = "steelblue")) +
  scale_linetype_manual(values = c("35" = "dashed",
                                   "60" = "longdash")) +
  scale_shape_manual(values = c("35" = 17,
                                "60" = 15)) +
  geom_point(size=4) +
  geom_linerange(aes(ymin= CI.mean - CI.sd, ymax = CI.mean + CI.sd)) +
  geom_line(aes(y=CI.mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show.legend = FALSE) +
  # Add annotation for tillage system differences #
  annotate("segment", x = PR.Untrafficked.TillDiff$Plot.Depth +0.4, xend = PR.Untrafficked.TillDiff$Plot.Depth +0.4, y = -0.1, yend = -0.1 +PR.Untrafficked.TillDiff$Diff, color = "black", size=1) +
  annotate("text", x = PR.Untrafficked.TillDiff$Plot.Depth + 2.4, y = -0.1, label = PR.Untrafficked.TillDiff$Signif, size = 10, color="black", hjust=0) +
  xlim(50,0) +
  ylim(-0.1,2.1) +
  ylab(expression(Penetration~Resistance~group("(",MPa,")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = "none") +
  labs(color = "Stover\nRemoved (%)", shape = "Stover\nRemoved (%)")
ggsave(paste(FigureFP,"NT_CC_PR_Untrafficked.jpg",sep=""),
       width=4, height = 5, units = "in") 


#Compare Chisel Plow v No-Till at Med and High Residue Removal Levels
HighRemoval_CC_Only<-filter(CI.df, ResidueRemoved=="100", Crop=="CC")
NoLowRemoval_0to5cm <- filter(CI.df, ResidueRemoved!='0',Crop=="CC", Depth=='0-5')
ggplot(NoLowRemoval_0to5cm, aes(x=Tillage, y=ConeIndex)) +
  geom_boxplot(show.legend=FALSE) +
  ylab("Cone Index (MPa)") +
  ggtitle("Tillage Impact at Medium and High Residue Removal, 0-5 cm") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(rows=vars(Wheel), cols=vars(ResidueRemoved),
             labeller = labeller(.cols = label_both)) +
  theme_bw(base_size=16)

NoLowRemoval_5to15cm <- filter(CI.df, ResidueRemoved!='0',Crop=="CC", Depth=='5-15')
ggplot(NoLowRemoval_5to15cm, aes(x=Tillage, y=ConeIndex)) +
  geom_boxplot(show.legend=FALSE) +
  ylab("Cone Index (MPa)") +
  ggtitle("Tillage Impact at Medium and High Residue Removal, 5-15 cm") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(rows=vars(Wheel), cols=vars(ResidueRemoved),
             labeller = labeller(.cols = label_both)) +
  theme_bw(base_size=16)

NoLowRemoval_15to30cm <- filter(CI.df, ResidueRemoved!='0',Crop=="CC", Depth=='15-30')
ggplot(NoLowRemoval_15to30cm, aes(x=Tillage, y=ConeIndex)) +
  geom_boxplot(show.legend=FALSE) +
  ylab("Cone Index (MPa)") +
  ggtitle("Tillage Impact at Medium and High Residue Removal, 15-30 cm") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(rows=vars(Wheel), cols=vars(ResidueRemoved),
             labeller = labeller(.cols = label_both)) +
  theme_bw(base_size=16)

NoLowRemoval_30to60cm <- filter(CI.df, ResidueRemoved!='0',Crop=="CC", Depth=='30-60')
ggplot(NoLowRemoval_30to60cm, aes(x=Tillage, y=ConeIndex)) +
  geom_boxplot(show.legend=FALSE) +
  ylab("Cone Index (MPa)") +
  ggtitle("Tillage Impact at Medium and High Residue Removal, 30-60 cm") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(rows=vars(Wheel), cols=vars(ResidueRemoved),
             labeller = labeller(.cols = label_both)) +
  theme_bw(base_size=16)




# Analyze Tillage X Residue and Traffic for 35% and 60% residue removal ####
No0RR_CC_0to5<-filter(CI.df,ResidueRemoved != '0', Crop == 'CC', Depth == '0-5')
dim(No0RR_CC_0to5)

No0RR_CC_5to15<-filter(CI.df,ResidueRemoved != '0', Crop == 'CC', Depth == '5-15')
dim(No0RR_CC_5to15)

No0RR_CC_15to30<-filter(CI.df,ResidueRemoved != '0', Crop == 'CC', Depth == '15-30')
dim(No0RR_CC_15to30)

No0RR_CC_30to60<-filter(CI.df,ResidueRemoved != '0', Crop == 'CC', Depth == '30-60')
dim(No0RR_CC_30to60)

# Plot data (box plots)
ggplot(No0RR_CC_0to5, aes(x=Tillage, y=ConeIndex)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Tillage and Residue Removal Impacts, 0 to 5 cm") +
  ylab("Cone Index (MPa)") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(cols=vars(Wheel), rows=vars(ResidueRemoved),
             labeller = labeller(.rows = label_both)) +
  theme_bw(base_size=16)

ggplot(No0RR_CC_5to15, aes(x=Tillage, y=ConeIndex)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Tillage and Residue Removal Impacts, 5 to 15 cm") +
  ylab("Cone Index (MPa)") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(cols=vars(Wheel), rows=vars(ResidueRemoved),
             labeller = labeller(.rows = label_both)) +
  theme_bw(base_size=16)

ggplot(No0RR_CC_15to30, aes(x=Tillage, y=ConeIndex)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Tillage and Residue Removal Impacts, 15 to 30 cm") +
  ylab("Cone Index (MPa)") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(cols=vars(Wheel), rows=vars(ResidueRemoved),
             labeller = labeller(.rows = label_both)) +
  theme_bw(base_size=16)

ggplot(No0RR_CC_30to60, aes(x=Tillage, y=ConeIndex)) +
  geom_boxplot(show.legend=FALSE) +
  ggtitle("Tillage and Residue Removal Impacts, 30 to 60 cm") +
  ylab("Cone Index (MPa)") +
  geom_jitter(color="black", size=1, alpha=0.9, width=0.3,show.legend=FALSE) +
  facet_grid(cols=vars(Wheel), rows=vars(ResidueRemoved),
             labeller = labeller(.rows = label_both)) +
  theme_bw(base_size=16)

#ANOVA Tables
No0RR_CC_0to5.aov = aov(ConeIndex ~ Block + Wheel * Tillage * ResidueRemoved +
                   Error(Block/Plot_2),No0RR_CC_0to5)
summary(No0RR_CC_0to5.aov, df = "Kenward-Roger", type = 1)

No0RR_CC_5to15.aov = aov(ConeIndex ~ Block + Wheel * Tillage * ResidueRemoved + Error(Block/Plot_2),No0RR_CC_5to15)
summary(No0RR_CC_5to15.aov, df = "Kenward-Roger", type = 1)

No0RR_CC_15to30.aov = aov(ConeIndex ~ Block + Wheel * Tillage * ResidueRemoved + Error(Block/Plot_2),No0RR_CC_15to30)
summary(No0RR_CC_15to30.aov, df = "Kenward-Roger", type = 1)

No0RR_CC_30to60.aov = aov(ConeIndex ~ Block + Wheel * Tillage * ResidueRemoved + Error(Block/Plot_2),No0RR_CC_30to60)
summary(No0RR_CC_30to60.aov, df = "Kenward-Roger", type = 1)


#Means and SEs
No0RR_CC_0to5.means = lmer(ConeIndex ~ Block + Wheel * Tillage * ResidueRemoved + (1|Block:Plot_2), data=No0RR_CC_0to5)
anova(No0RR_CC_0to5.means, df = "Kenward-Roger", type = 1)
plot(No0RR_CC_0to5.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "No0RR_CC_0to5")
emmeans::emmeans(No0RR_CC_0to5.means, ~Tillage)
emmeans::emmeans(No0RR_CC_0to5.means, ~Wheel)
#emmeans::emmeans(No0RR_CC_0to5.means, ~Residue)
#emmeans::emmeans(No0RR_CC_0to5.means, ~Tillage * Wheel)

No0RR_CC_5to15.means = lmer(ConeIndex ~ Block + Wheel * Tillage * ResidueRemoved + (1|Block:Plot_2), data=No0RR_CC_5to15)
anova(No0RR_CC_5to15.means, df = "Kenward-Roger", type = 1)
plot(No0RR_CC_5to15.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "No0RR_CC_5to15")
emmeans::emmeans(No0RR_CC_5to15.means, ~Tillage)
emmeans::emmeans(No0RR_CC_5to15.means, ~Wheel)
emmeans::emmeans(No0RR_CC_5to15.means, ~Tillage * Wheel)

No0RR_CC_15to30.means = lmer(ConeIndex ~ Block + Wheel * Tillage * ResidueRemoved + (1|Block:Plot_2), data=No0RR_CC_15to30)
anova(No0RR_CC_15to30.means, df = "Kenward-Roger", type = 1)
plot(No0RR_CC_15to30.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "No0RR_CC_15to30")
emmeans::emmeans(No0RR_CC_15to30.means, ~Tillage)
emmeans::emmeans(No0RR_CC_15to30.means, ~Wheel)
emmeans::emmeans(No0RR_CC_15to30.means, ~Tillage * Wheel)

No0RR_CC_30to60.means = lmer(ConeIndex ~ Block + Wheel * Tillage * ResidueRemoved + (1|Block:Plot_2), data=No0RR_CC_30to60)
anova(No0RR_CC_30to60.means, df = "Kenward-Roger", type = 1)
plot(No0RR_CC_30to60.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "No0RR_CC_30to60")
emmeans::emmeans(No0RR_CC_30to60.means, ~Tillage)
emmeans::emmeans(No0RR_CC_30to60.means, ~Wheel)
emmeans::emmeans(No0RR_CC_30to60.means, ~ResidueRemoved * Wheel)


#REML constrasts and sed's for qualitative residue removal, tillage effects, and traffic
w.t.0to5 = emmeans::emmeans(No0RR_CC_0to5.means, ~Wheel|Tillage)
emmeans::contrast(w.t.0to5, alpha = 0.05, method = "pairwise")
t.w.0to5 = emmeans::emmeans(No0RR_CC_0to5.means, ~Tillage|Wheel)
emmeans::contrast(t.w.0to5, alpha = 0.05, method = "pairwise")
w.0to5 = emmeans::emmeans(No0RR_CC_0to5.means, ~Wheel)
emmeans::contrast(w.0to5, alpha = 0.05, method = "pairwise")
t.0to5 = emmeans::emmeans(No0RR_CC_0to5.means, ~Tillage)
emmeans::contrast(t.0to5, alpha = 0.05, method = "pairwise")
t.r.0to5 = emmeans::emmeans(No0RR_CC_0to5.means, ~Tillage|ResidueRemoved)
emmeans::contrast(t.r.0to5, alpha = 0.05, method = "pairwise")


w.t.5to15 = emmeans::emmeans(No0RR_CC_5to15.means, ~Wheel|Tillage)
emmeans::contrast(w.t.5to15, alpha = 0.05, method = "pairwise")
t.w.5to15 = emmeans::emmeans(No0RR_CC_5to15.means, ~Tillage|Wheel)
emmeans::contrast(t.w.5to15, alpha = 0.05, method = "pairwise")
w.5to15 = emmeans::emmeans(No0RR_CC_5to15.means, ~Wheel)
emmeans::contrast(w.5to15, alpha = 0.05, method = "pairwise")
t.5to15 = emmeans::emmeans(No0RR_CC_5to15.means, ~Tillage)
emmeans::contrast(t.5to15, alpha = 0.05, method = "pairwise")
t.r.5to15 = emmeans::emmeans(No0RR_CC_5to15.means, ~Tillage|ResidueRemoved)
emmeans::contrast(t.r.5to15, alpha = 0.05, method = "pairwise")

# Analyze BD and WC in model with tillage and RR, using only 35 and 60% RR ####
# This is the same code as above to make tibbles for each depth.
No0RR_CC_0to5<-filter(CI.df,ResidueRemoved != '0', Crop == 'CC', Depth == '0-5')
dim(No0RR_CC_0to5)

No0RR_CC_5to15<-filter(CI.df,ResidueRemoved != '0', Crop == 'CC', Depth == '5-15')
dim(No0RR_CC_5to15)

No0RR_CC_15to30<-filter(CI.df,ResidueRemoved != '0', Crop == 'CC', Depth == '15-30')
dim(No0RR_CC_15to30)

No0RR_CC_30to60<-filter(CI.df,ResidueRemoved != '0', Crop == 'CC', Depth == '30-60')
dim(No0RR_CC_30to60)


#Analyze BD
No0RR_CC_0to5_BD.aov = aov(BD ~ Block + Tillage * ResidueRemoved,No0RR_CC_0to5)
summary(No0RR_CC_0to5_BD.aov)

#Means and SEs
No0RR_CC_0to5_BD.means = lmer(BD ~ Block + Tillage * ResidueRemoved + (1|Block:Plot_2), data=No0RR_CC_0to5)
anova(No0RR_CC_0to5_BD.means, df = "Kenward-Roger", type = 1)
plot(No0RR_CC_0to5_BD.means, sub.caption = NA, ylab= "Residuals", xlab = "Fitted", main = "No0RR_CC_0to5")
emmeans::emmeans(No0RR_CC_0to5_BD.means, ~Tillage)
emmeans::emmeans(No0RR_CC_0to5_BD.means, ~ResidueRemoved)
emmeans::emmeans(No0RR_CC_0to5_BD.means, ~Tillage * ResidueRemoved)

t.0to5 = emmeans::emmeans(No0RR_CC_0to5_BD.means, ~Tillage)
emmeans::contrast(t.0to5, alpha = 0.05, method = "pairwise")



No0RR_CC_5to15_BD.aov = aov(BD ~ Block + Tillage * ResidueRemoved, No0RR_CC_5to15)
summary(No0RR_CC_5to15_BD.aov)
t.5to15 = emmeans::emmeans(No0RR_CC_5to15_BD.aov, ~Tillage)
emmeans::contrast(t.5to15, alpha = 0.05, method = "pairwise")



No0RR_CC_15to30_BD.aov = aov(BD ~ Block + Tillage * ResidueRemoved, No0RR_CC_15to30)
summary(No0RR_CC_15to30_BD.aov)

No0RR_CC_30to60_BD.aov = aov(BD ~ Block + Tillage * ResidueRemoved, No0RR_CC_30to60)
summary(No0RR_CC_30to60_BD.aov)



# Analyze GWC
No0RR_CC_0to5_GWC.aov = aov(GWC ~ Block + Tillage * ResidueRemoved,No0RR_CC_0to5)
summary(No0RR_CC_0to5_GWC.aov)

No0RR_CC_5to15_GWC.aov = aov(GWC ~ Block + Tillage * ResidueRemoved, No0RR_CC_5to15)
summary(No0RR_CC_5to15_GWC.aov)

No0RR_CC_15to30_GWC.aov = aov(GWC ~ Block + Tillage * ResidueRemoved, No0RR_CC_15to30)
summary(No0RR_CC_15to30_GWC.aov)

No0RR_CC_30to60_GWC.aov = aov(GWC ~ Block + Tillage * ResidueRemoved, No0RR_CC_30to60)
summary(No0RR_CC_30to60_GWC.aov)


# Analyze SOC
No0RR_CC_0to5_TC.aov = aov(TC.perc ~ Block + Tillage * ResidueRemoved,No0RR_CC_0to5)
summary(No0RR_CC_0to5_TC.aov)

No0RR_CC_5to15_TC.aov = aov(TC.perc ~ Block + Tillage * ResidueRemoved,No0RR_CC_5to15)
summary(No0RR_CC_5to15_TC.aov)

No0RR_CC_15to30_TC.aov = aov(TC.perc ~ Block + Tillage * ResidueRemoved,No0RR_CC_15to30)
summary(No0RR_CC_15to30_TC.aov)

No0RR_CC_30to60_TC.aov = aov(TC.perc ~ Block + Tillage * ResidueRemoved,No0RR_CC_30to60)
summary(No0RR_CC_30to60_TC.aov)



# Plot BD profile
No0RR_CC_Summary <- filter(CI.df,ResidueRemoved != '0', Crop == 'CC') %>%
  mutate(Depth.Midpoint = (Depth.Upper + Depth.Lower)/2) %>%
  group_by(Tillage, Wheel, ResidueRemoved, Depth.Midpoint) %>%
  summarise(CI.mean = mean(ConeIndex, na.rm = TRUE),
            CI.sd = sd(ConeIndex, na.rm = TRUE),
            BD.mean = mean(BD),
            BD.sd = sd(BD),
            GWC.mean = mean(GWC),
            GWC.sd = sd(GWC),
            VWC.mean = mean (VWC),
            VWC.sd = sd(VWC))

No0RR_CC_Summary$Plot.Depth <- No0RR_CC_Summary$Depth.Midpoint
No0RR_CC_Summary[No0RR_CC_Summary$ResidueRemoved==35,'Plot.Depth'] <- No0RR_CC_Summary[No0RR_CC_Summary$ResidueRemoved==35,'Depth.Midpoint'] + 0.4
No0RR_CC_Summary[No0RR_CC_Summary$ResidueRemoved==60,'Plot.Depth'] <- No0RR_CC_Summary[No0RR_CC_Summary$ResidueRemoved==60,'Depth.Midpoint'] + 0.8

No0RR_CC_Untrafficked <- filter(No0RR_CC_Summary, Wheel=="Untrafficked")

ggplot(No0RR_CC_Untrafficked, aes(x=Plot.Depth, y=BD.mean, shape=Tillage,col=Tillage)) +
  scale_color_manual(values = c("CP" = "purple",
                                "NT" ="orange")) +
  geom_point(size=3) +
  geom_linerange(aes(ymin= BD.mean - BD.sd, ymax = BD.mean + BD.sd)) +
  geom_line() +
  xlim(50,0) +
  ylab(expression(Bulk~Density~group("(",g~cm^{-3},")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  facet_grid(~ResidueRemoved) +
  theme_classic() +
  theme(text = element_text(size = 15)) #+
#theme(legend.position = c(0.9, 0.9))
ggsave(paste(FigureFP,"No0RR_CC_BulkDensity.jpg",sep=""),
       width=6, height = 5, units = "in") 

# Plot GWC profile
ggplot(No0RR_CC_Untrafficked, aes(x=Plot.Depth, y=GWC.mean, shape=Tillage,col=Tillage)) +
  scale_color_manual(values = c("CP" = "purple",
                                "NT" ="orange")) +
  geom_point(size=3) +
  geom_linerange(aes(ymin= GWC.mean - GWC.sd, ymax = GWC.mean + GWC.sd)) +
  geom_line() +
  xlim(50,0) +
  ylab(expression(Soil~Water~Content~group("(",g~g^{-1},")"))) +
  xlab("Depth, Midpoint (cm)") +
  coord_flip() +
  facet_grid(~ResidueRemoved) +
  theme_classic() +
  theme(text = element_text(size = 15)) #+
#theme(legend.position = c(0.9, 0.9))
ggsave(paste(FigureFP,"No0RR_CC_GWC.jpg",sep=""),
       width=6, height = 5, units = "in") 


# Average stover and grain yields  2008-2020 #####
Yield.df<-read.csv(paste(FP,"Field 70-71 CornYield_2008-2021_ForR.csv", sep=""))
dim(Yield.df);names(Yield.df)

# Analyze treatment means for Stover yield
Stover.long <- pivot_longer(Yield.df,cols = starts_with("Stover"),
                            names_to = "Year",
                            names_prefix = "Stover",
                            values_to = "Stover",
                            values_drop_na = TRUE)
Stover.long <- Stover.long %>% 
  mutate(Treatment = as.factor(Treatment), 
         ResidueRemoved = as.factor(LevelStoverHarvest), 
         ResidueRemoved = fct_recode(ResidueRemoved, "0" = "None","35" = "Moderate","60"="High"),
         ResidueRemoved = factor(ResidueRemoved, levels=c("0","35","60")),
         Tillage = as.factor(Tillage)) %>%  select(!starts_with('Grain'))

Stover.CC <- filter(Stover.long, Treatment %in% c("1","3","4","5","6"))

Stover_byTx <- Stover.CC  %>%
  group_by(Treatment) %>%
  summarize(
    Mean=mean(Stover, na.rm=TRUE) * 2.24,
    Min = min(Stover, na.rm=TRUE) * 2.24,
    Max = max(Stover, na.rm=TRUE) * 2.24,
    SD = sd(Stover, na.rm=TRUE) * 2.24,
    N = n())

Stover_byLevel <- Stover.CC %>%
  group_by(LevelStoverHarvest) %>%
  summarize(
    Mean=mean(Stover, na.rm=TRUE) * 2.24,
    Min = min(Stover, na.rm=TRUE) * 2.24,
    Max = max(Stover, na.rm=TRUE) * 2.24,
    SD = sd(Stover, na.rm=TRUE) * 2.24,
    N = n())

Stover.aov1 <- lm(Stover ~ Rep + Treatment, data = Stover.CC)
anova(Stover.aov1)
(Tx.Stover = emmeans::emmeans(Stover.aov1, ~Treatment))
emmeans::contrast(Tx.Stover, alpha = 0.05, method = "pairwise")

Stover.aov2 <- lm(Stover ~ Rep + ResidueRemoved * Tillage, data = Stover.CC)
anova(Stover.aov2)
plot(Stover.aov2)
(Till = emmeans::emmeans(Stover.aov2, ~Tillage))
(Res = emmeans::emmeans(Stover.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Stover.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")


# Analyze treatment means for Grain yield 
Grain.long <- pivot_longer(Yield.df,cols = starts_with("Grain"),
                           names_to = "Year",
                           names_prefix = "Grain",
                           values_to = "Grain",
                           values_drop_na = TRUE)
Grain.long <- Grain.long %>% 
  mutate(Treatment = as.factor(Treatment), 
         ResidueRemoved = as.factor(LevelStoverHarvest), 
         ResidueRemoved = fct_recode(ResidueRemoved, "0" = "None","35" = "Moderate","60"="High"),
         ResidueRemoved = factor(ResidueRemoved, levels=c("0","35","60")),
         Tillage = as.factor(Tillage)) %>%  
  select(!starts_with('Stover'))

Grain.CC <- filter(Grain.long, Treatment %in% c("1","3","4","5","6"))

# Convert from bu/acre to Mg/ha
Grain_byTx <- Grain.CC  %>%
  group_by(Treatment) %>%
  summarize(
    Mean=mean(Grain, na.rm=TRUE) / (39.37 * 0.405),
    Min = min(Grain, na.rm=TRUE) / (39.37 * 0.405),
    Max = max(Grain, na.rm=TRUE) / (39.37 * 0.405),
    SD = sd(Grain, na.rm=TRUE) / (39.37 * 0.405),
    N = n())

# Convert from bu/acre to Mg/ha
Grain_byLevel <- Grain.CC %>%
  group_by(ResidueRemoved) %>%
  summarize(
    Mean=mean(Grain, na.rm=TRUE) / (39.37 * 0.405),
    Min = min(Grain, na.rm=TRUE) / (39.37 * 0.405),
    Max = max(Grain, na.rm=TRUE) / (39.37 * 0.405),
    SD = sd(Grain, na.rm=TRUE) / (39.37 * 0.405),
    N = n())

Grain.aov1 <- lm(Grain ~ Rep + Treatment, data = Grain.CC)
anova(Grain.aov1)#, df = "Kenward-Roger", type = 1)
plot(Grain.aov1)
(Tx.Grain = emmeans::emmeans(Grain.aov1, ~Treatment))
emmeans::contrast(Tx.Grain, alpha = 0.05, method = "pairwise")

Grain.aov2 <- lm(Grain ~ Rep + ResidueRemoved * Tillage, data = Grain.CC)
anova(Grain.aov2)
#plot(Grain.aov2)
(Till = emmeans::emmeans(Grain.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")
# Rainfall 2008-2020 #####
# Data obtained from interpolated Iowa Mesonet product #
# https://mesonet.agron.iastate.edu/rainfall/
Rainfall <- read.csv(paste(FP,"Rainfall_AEA.csv",sep=""))
dim(Rainfall); names(Rainfall)

# I don't have exact planting and harvest dates, so get May through August total precip
Rainfall_byGrowSeas <- Rainfall %>%
  filter(Month %in% 5:8, Year < 2021) %>%
  group_by(Year) %>%
  summarize(Rainfall = sum(mm)/10)

# Combine with average May temperatures from PRISM
# Details: http://www.prism.oregonstate.edu/documents/PRISM_datasets.pdf
# PRISM Time Series Data
# Location:  Lat: 42.0176   Lon: -93.7645   Elev: 325m
# Climate variables: tmin,tmean,tmax
# Spatial resolution: 4km
# Period: 2008-05 - 2021-05
# Dataset: AN81m
# PRISM day definition: 24 hours ending at 1200 UTC on the day shown
# Grid Cell Interpolation: Off
# Time series generated: 2022-Sep-21

MayTemps <- read.csv(paste(FP,"PRISM_MayTemps.csv",sep=""))
dim(MayTemps); names(MayTemps)

WeatherData<-merge(Rainfall_byGrowSeas,MayTemps[,2:5],by='Year')

ggplot(WeatherData, aes(x=Year)) +
  geom_bar(aes(y=Rainfall/3, fill="TotPrecip"), stat="identity", show.legend = FALSE) +
  geom_point(aes(y=May.tmean.C), size=3) +
  geom_line(aes(y=May.tmean.C), size=2) +
  scale_x_continuous(breaks=2008:2020, expand = expansion(mult=0.03)) +
  scale_y_continuous(
    expression("Mean Temp, May " (degree*C)),
    sec.axis = sec_axis(~ . *3, name = "Rainfall, May-Sept (cm)")) +
  scale_colour_manual("", values = c("Temperature" = "black")) +
  scale_fill_manual("", values = "orange") +
  theme(text = element_text(size=16),
        axis.text.x = element_text(angle=90, hjust=1),
        axis.ticks.length=unit(-0.25, "cm")) +
  theme_classic(base_size=16) #+
  #theme(text = element_text(size = 14),
   #     axis.ticks.length=unit(-0.25, "cm")) 
ggsave(paste(FigureFP,"Precip_MayTemp.jpg",sep=""),
       width=10.5, height = 3, units = "in") 

# Merge total rainfall with Grain.CC
Grain.CC<-merge(Grain.CC, Rainfall_byGrowSeas,by='Year' )
#Grain.CC <- mutate(Grain.CC, Year = as.numeric(Year))

# Plot Average grain by year ####
Grain_byYear <- Grain.CC %>%
  group_by(ResidueRemoved,Tillage,Year) %>%
  summarize(
    Mean=mean(Grain, na.rm=TRUE) / (39.37 * 0.405),
    SD = sd(Grain, na.rm=TRUE) / (39.37 * 0.405))


ggplot(Grain_byYear, aes(x=Year,ymin = Mean-SD, ymax=Mean + SD, color=ResidueRemoved, shape = ResidueRemoved)) +
   scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                 "60" = "steelblue")) +
  geom_linerange(size=1) +
  geom_line(aes(y=Mean, linetype=ResidueRemoved, group=ResidueRemoved),size=1, show_guide = FALSE) +
  geom_point(aes(y=Mean, group=ResidueRemoved),size = 3) +
  facet_grid(rows=vars(Tillage)) +
  ylab(expression(Grain~Yield~group("(",Mg~ha^{-1}, ")"))) +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = c(0.63, 0.6)) +
  labs(color = "Stover\nRemoved (%)", shape = "Stover\nRemoved (%)")

ggsave(paste(FigureFP,"GrainYields.jpg",sep=""),
       width=10, height = 5, units = "in") 

# Plot average grain over all years, with scatter showing 4 Reps

Grain_byPlot <- Grain.CC %>%
  group_by(ResidueRemoved,Tillage,Rep) %>%
  summarize(
    Mean=mean(Grain, na.rm=TRUE) / (39.37 * 0.405),
    SD = sd(Grain, na.rm=TRUE) / (39.37 * 0.405))

ggplot(Grain_byPlot, aes(x=ResidueRemoved, y=Mean, color=ResidueRemoved)) +
  scale_color_manual(values = c("0" = "purple",
                                "35" ="orange",
                                "60" = "steelblue")) +
  geom_boxplot()+
  geom_jitter(width=0.1)+
  facet_grid(rows=vars(Tillage)) +
  ylab(expression(Mean~Grain~Yield~group("(",Mg~ha^{-1}, ")"))) +
  xlab('Stover Removed (%)') +
  ylim(4,16) +
  theme_classic() +
  theme(text = element_text(size = 16),
        axis.ticks.length=unit(-0.25, "cm"),
        legend.position = "none")
  
ggsave(paste(FigureFP,"GrainYields_boxplot.jpg",sep=""),
       width=3, height = 5, units = "in")  

# Analyze grain yield with a repeated measures model ####

# Following agritutorial example 4, first select the var-covar structure using a saturated
# model for treatments and time that considers all treatment factors and time as qualitative
class(Grain.CC$Year)
Grain.CC$YearFact <- as.factor(Grain.CC$Year)
class(Grain.CC$Rep)
Grain.CC$PlotNo <- as.factor(Grain.CC$PlotNo)

# gls cannot handle missing values, so I included Treatment
# rather than tillage and residue in the model
Grain.gls1 <- gls(Grain ~ YearFact * (Rep + Treatment), 
                  corr = corExp(form = ~Year|PlotNo), Grain.CC)
anova(Grain.gls1)
AIC = AIC(Grain.gls1)
logLik = logLik(Grain.gls1)
Variogram(Grain.gls1)

Grain.gls2 <- gls(Grain ~ YearFact * (Rep + Treatment), 
                  corr = corExp(form = ~Year|PlotNo, nugget = TRUE), Grain.CC)
anova(Grain.gls2)
AIC = c(AIC, AIC(Grain.gls2))
logLik = c(logLik, logLik(Grain.gls2))
Variogram(Grain.gls2)

Grain.gls3 <- gls(Grain ~ YearFact * (Rep + Treatment), corr = corSymm(form = ~1|PlotNo), 
                  weights = varIdent(form = ~1|Year), 
                  Grain.CC)
anova(Grain.gls3)
AIC = c(AIC, AIC(Grain.gls3))
logLik = c(logLik, logLik(Grain.gls3))
Variogram(Grain.gls3)


# I will use the corExp without nugget
Grain.gls4 <- gls(Grain ~ Rep + Treatment, 
                  corr = corExp(form = ~Year|PlotNo, nugget = TRUE), Grain.CC)
anova(Grain.gls4)
summary(Grain.gls4)
(Tx = emmeans::emmeans(Grain.gls4, ~Treatment))
emmeans::contrast(Tx, alpha = 0.05, method = "pairwise")
# Set up contrast between Tx 1 and 6 only
# Borrow function from here: https://cran.r-project.org/web/packages/emmeans/vignettes/comparisons.html#contrasts
# Didn't work


# Omit CP 0 and look at factorial study
Grain.No0CP <- Grain.CC %>% filter(LevelStoverHarvest != "None")
dim(Grain.CC)
dim(Grain.No0CP)

Grain.gls5 <- gls(Grain ~ Rep + Tillage * ResidueRemoved, 
                  corr = corExp(form = ~Year|PlotNo, nugget = TRUE), Grain.No0CP)
anova(Grain.gls5)
summary(Grain.gls5)
(Till = emmeans::emmeans(Grain.gls5, ~Tillage))
(Res = emmeans::emmeans(Grain.gls5, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain.gls5, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")



Grain.aov2 <- gls(Grain ~ ResidueRemoved * Tillage, corr = cordata = Grain.CC)
anova(Grain.aov2)
#plot(Grain.aov2)
(Till = emmeans::emmeans(Grain.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")




# Get stats for grain yield in each year ####
#2008
Grain2008.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2008))
anova(Grain2008.aov)#
plot(Grain2008.aov)

Grain2008.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2008))
anova(Grain2008.aov2)

#2009
Grain2009.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2009))
anova(Grain2009.aov)#
plot(Grain2009.aov)

Grain2009.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2009))
anova(Grain2009.aov2)

(Till = emmeans::emmeans(Grain2009.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2009.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2009.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2010
Grain2010.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2010))
anova(Grain2010.aov)#
plot(Grain2010.aov)

Grain2010.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2010))
anova(Grain2010.aov2)

(Till = emmeans::emmeans(Grain2010.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2010.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2010.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")


#2011
Grain2011.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2011))
anova(Grain2011.aov)#
plot(Grain2011.aov)

Grain2011.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2011))
anova(Grain2011.aov2)
(Till = emmeans::emmeans(Grain2011.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2011.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2011.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2012
Grain2012.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2012))
anova(Grain2012.aov)#
#plot(Grain2012.aov)

Grain2012.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2012))
anova(Grain2012.aov2)
(Till = emmeans::emmeans(Grain2012.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2012.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2012.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2013
Grain2013.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2013))
anova(Grain2013.aov)#

Grain2013.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2013))
anova(Grain2013.aov2)
(Till = emmeans::emmeans(Grain2013.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2013.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2013.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2014
Grain2014.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2014))
anova(Grain2014.aov)#

Grain2014.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2014))
anova(Grain2014.aov2)
(Till = emmeans::emmeans(Grain2014.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2014.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2014.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2015
Grain2015.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2015))
anova(Grain2015.aov)#
#plot(Grain2015.aov)

Grain2015.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2015))
anova(Grain2015.aov2)
(Till = emmeans::emmeans(Grain2015.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2015.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2015.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2016
Grain2016.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2016))
anova(Grain2016.aov)#
#plot(Grain2016.aov)

Grain2016.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2016))
anova(Grain2016.aov2)
(Till = emmeans::emmeans(Grain2016.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2016.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2016.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2017
Grain2017.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2017))
anova(Grain2017.aov)#
#plot(Grain2017.aov)

Grain2017.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2017))
anova(Grain2017.aov2)
(Till = emmeans::emmeans(Grain2017.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2017.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2017.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2018
Grain2018.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2018))
anova(Grain2018.aov)#
#plot(Grain2018.aov)

Grain2018.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2018))
anova(Grain2018.aov2)
(Till = emmeans::emmeans(Grain2018.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2018.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2018.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2019
Grain2019.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2019))
anova(Grain2019.aov)#

Grain2019.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2019))
anova(Grain2019.aov2)
(Till = emmeans::emmeans(Grain2019.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2019.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2019.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

#2020
Grain2020.aov <- lm(Grain ~ Rep + Treatment, data = Grain.CC, subset=c(Year==2020))
anova(Grain2020.aov)#

Grain2020.aov2 <- lm(Grain ~ Rep + Tillage * ResidueRemoved, data = Grain.CC, subset=c(Year==2020))
anova(Grain2020.aov2)
(Till = emmeans::emmeans(Grain2020.aov2, ~Tillage))
(Res = emmeans::emmeans(Grain2020.aov2, ~ResidueRemoved))
(TillxRes = emmeans::emmeans(Grain2020.aov2, ~Tillage * ResidueRemoved))
emmeans::contrast(TillxRes, alpha = 0.05, method = "pairwise")
emmeans::contrast(Till, alpha = 0.05, method = "pairwise")
emmeans::contrast(Res, alpha = 0.05, method = "pairwise")

