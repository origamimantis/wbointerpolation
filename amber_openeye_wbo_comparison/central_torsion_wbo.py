
import cmiles
import collections
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import qcportal as ptl
import time
 
from openeye import oechem, oeomega, oequacpac
from openforcefield.topology import Molecule, Topology
from openforcefield.typing.engines.smirnoff import ForceField

#Setup
client = ptl.FractalClient()
torsion_datasets = client.list_collections("TorsionDriveDataset")
datasets = []
for i in range(len(torsion_datasets)):
    datasets.append(torsion_datasets.index[i][1])

def get_data(datasets):
    """Loads data from a QC archive dataset"""
    data_dict={}
    for dataset_name in datasets:
        count = 0
        while True:
            try:
                ds = client.get_collection("TorsionDriveDataset", dataset_name)
                ds.status("default", status="COMPLETE")
                break
            except:
                time.sleep(20)
                count += 1
                if count < 2:
                    continue
                else:
                    break

        params = []
        for index in ds.df.index:
            # get the dihedral indices
            dihedral_indices = ds.df.loc[index].default.keywords.dihedrals[0]
            cmiles=ds.get_entry(index).attributes['canonical_isomeric_explicit_hydrogen_mapped_smiles']
            data_dict[cmiles]=dihedral_indices

        counter = collections.Counter(params)
        print(dataset_name, counter)
        print(" ")
    return data_dict

def smiles2oemol(smiles):
    """
    Conforms molecules from a smiles string to an OEMol with all the traits
    necessary for OpenEye functions to return accurate data
    """
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    #initialize omega
    omega = oeomega.OEOmega()
    omega.SetMaxConfs(1)
    omega.SetIncludeInput(True)
    omega.SetCanonOrder(True)
    omega.SetSampleHydrogens(True)
    omega.SetStrictStereo(False)
    omega.SetStrictAtomTypes(True)
    omega.SetIncludeInput(False)
    status = omega(mol)
    
    return (mol, status)

def wiberg_bond_order(mol, bond_idxs):
    """Calculates the Wiberg Bond Order for a specified bond"""
    #Construction for WBO calculation
    AM1_CALCULATOR = oequacpac.OEAM1()
    results = oequacpac.OEAM1Results()
    
    AM1_CALCULATOR.CalcAM1(results, mol)
    
    return results.GetBondOrder(bond_idxs[0], bond_idxs[1])
    
def visualize_benchmark(group_num, wbo_values):
    """Creates a double bar graph to visualize the wbo value comparisons"""
    width = .35
    
    fig, ax = plt.subplots()
    torsion_set1 = []
    torsion_set2 = []
    
    for key, values in wbo_values.items():
        torsion_set1.append(values[0])
        torsion_set2.append(values[1])
    
    x = np.arange(len(wbo_values.keys()))
    
    ax.bar(x - width/2, torsion_set1, color = "#236AB9", width = width, label="Torsion 1")
    ax.bar(x + width/2, torsion_set2, color = "#FF7F50", width = width, label="Torsion 2") #64A9F7
    
    ax.set_ylabel("Wiberg Bond Order", fontweight = "bold")
    ax.set_xlabel("Molecule, Torsion indices", fontweight = "bold")
    ax.set_xticks(x)
    ax.set_xticklabels(wbo_values.keys(), rotation = 90)
    ax.set_title(f"WBO Benchmark Group Number {group_num}")

    ax.legend(["Torsion 1", "Torsion 2"])
    plt.savefig(f"QCA_WBO_figures/QCA_WBO_benchmark Group Number{group_num}.png", bbox_inches = "tight")
    
def main():
    dataset_substitutedphenyl = ['OpenFF Substituted Phenyl Set 1']
    data = get_data(dataset_substitutedphenyl)
    
    benchmark_data = []
    
    wbo_values = {}
    count = 0
    for cmiles, indices in data.items():
        #Create an OEMol object for WBO calculation
        mol, status = smiles2oemol(cmiles)
        
        #Find the correct bonds based on the central torsion indices
        for bond in mol.GetBonds():
            if bond.GetIdx() == indices[1]:
                bond1_idxs = (bond.GetBgn().GetIdx(), bond.GetEnd().GetIdx())
            elif bond.GetIdx() == indices[2]:
                bond2_idxs = (bond.GetBgn().GetIdx(), bond.GetEnd().GetIdx())
        
        #Calculate the WBO value
        wbo_values[(cmiles, indices[1:3])] = (wiberg_bond_order(mol, bond1_idxs),
                                        wiberg_bond_order(mol, bond2_idxs))
        
        #Groups the data into sets of 25 for better visualization
        count += 1
        if count % 25 == 0 or count == len(data):
            benchmark_data.append(wbo_values)
            wbo_values = {}
            group_count = 0
    
    #Creates a visual of the wbo values for comparison
    for group_num, wbo_values in enumerate(benchmark_data):
        visualize_benchmark(group_num+1, wbo_values)

if __name__ == "__main__":
    main()