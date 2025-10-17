export const sampleMolecules = [
  {
    id: 'water',
    label: 'Water',
    formula: 'H₂O',
    description: 'Bent triatomic molecule with polar covalent bonds.',
    molecule: {
      id: 'sample-water',
      smiles: 'O',
      minimized: true,
      atoms: [
        { index: 0, element: 'O', x: 0, y: 0, z: 0 },
        { index: 1, element: 'H', x: 0.9572, y: 0.0, z: 0.0 },
        { index: 2, element: 'H', x: -0.2396, y: 0.927, z: 0.0 }
      ],
      bonds: [
        { atom1: 0, atom2: 1, order: 1 },
        { atom1: 0, atom2: 2, order: 1 }
      ]
    }
  },
  {
    id: 'carbon-dioxide',
    label: 'Carbon Dioxide',
    formula: 'CO₂',
    description: 'Linear molecule featuring double bonds between carbon and oxygen.',
    molecule: {
      id: 'sample-co2',
      smiles: 'O=C=O',
      minimized: false,
      atoms: [
        { index: 0, element: 'O', x: -1.16, y: 0, z: 0 },
        { index: 1, element: 'C', x: 0, y: 0, z: 0 },
        { index: 2, element: 'O', x: 1.16, y: 0, z: 0 }
      ],
      bonds: [
        { atom1: 0, atom2: 1, order: 2 },
        { atom1: 1, atom2: 2, order: 2 }
      ]
    }
  },
  {
    id: 'methane',
    label: 'Methane',
    formula: 'CH₄',
    description: 'Tetrahedral arrangement with a carbon atom surrounded by four hydrogens.',
    molecule: {
      id: 'sample-methane',
      smiles: 'C',
      minimized: false,
      atoms: [
        { index: 0, element: 'C', x: 0.0, y: 0.0, z: 0.0 },
        { index: 1, element: 'H', x: 0.629, y: 0.629, z: 0.629 },
        { index: 2, element: 'H', x: -0.629, y: -0.629, z: 0.629 },
        { index: 3, element: 'H', x: -0.629, y: 0.629, z: -0.629 },
        { index: 4, element: 'H', x: 0.629, y: -0.629, z: -0.629 }
      ],
      bonds: [
        { atom1: 0, atom2: 1, order: 1 },
        { atom1: 0, atom2: 2, order: 1 },
        { atom1: 0, atom2: 3, order: 1 },
        { atom1: 0, atom2: 4, order: 1 }
      ]
    }
  }
];
