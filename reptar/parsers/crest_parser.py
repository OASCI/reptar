# MIT License
#
# Copyright (c) 2022-2023, Alex M. Maldonado
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np
from ..extractors import ExtractorCREST
from .parser import Parser
from ..utils import atoms_by_number, parse_xyz


class ParserCREST(Parser):
    r"""Custom parser for CREST calculations."""

    def __init__(
        self,
        out_path=None,
        geom_path=None,
        traj_path=None,
        extractors=None,
        conformer_path=None,
        rotamer_path=None,
    ):
        """
        Parameters
        ----------
        out_path : :obj:`str`
            Path to the main log file generated by the package.
        geom_path : :obj:`str`, default: ``None``
            Not used.
        traj_path : :obj:`str`, default: ``None``
            Not used.
        extractors : :obj:`list`, default: ``None``
            Additional extractors for the parser to use.
        conformer_path : :obj:`str`, default: ``None``
            Conformer xyz file from CREST.
        rotamer_path : :obj:`str`, default: ``None``
            Rotamer xyz file from CREST.

        Notes
        -----
        Either ``conformer_path`` or ``rotamer_path`` should be provided.
        Specifying the type of crest xyz file is necessary for parsing the
        output file. If you are unsure, the rotamer file has more
        """
        self.package = "crest"
        if (traj_path is not None) and (geom_path is not None):
            raise ValueError("geom_path and traj_path are not supported for CREST")

        # We prefer the rotamer because it provides higher precision on
        # ensemble ratio.
        if (conformer_path is not None) and (rotamer_path is not None):
            raise ValueError("conformer_path and rotamer_path cannot both be provided")

        if rotamer_path is not None:
            self.xyz_type = "rotamer"
            self.xyz_path = rotamer_path
        elif conformer_path is not None:
            self.xyz_type = "conformer"
            self.xyz_path = conformer_path

        if extractors is None:
            extractors = []
        extractors.insert(0, ExtractorCREST(self.xyz_type))
        super().__init__(out_path, extractors)

        self.parsed_info["runtime_info"]["prov"] = "crest"

    def parse(self):
        r"""Parses trajectory file and extracts information."""
        # Extract information from output file.
        self.extract_data_out()

        # Extract atomic_numbers and geometry from conformer or rotamer.
        Z, comments, R = parse_xyz(self.xyz_path)

        # pylint: disable-next=R0801
        if len(set(tuple(i) for i in Z)) == 1:
            Z = Z[0]
        else:
            raise ValueError("Atomic numbers are not consistent.")
        Z = np.array(atoms_by_number(Z))
        self.parsed_info["system_info"]["atomic_numbers"] = Z

        R = np.array(R)
        if R.ndim == 2:
            R = np.array([R])
        assert R.ndim == 3
        self.parsed_info["system_info"]["geometry"] = R

        if self.xyz_type == "conformer":
            self.parsed_info["outputs"]["energy_ele"] = np.array(
                comments, dtype=np.float64
            )
        elif self.xyz_type == "rotamer":
            E, ensemble_weights = [], []
            for line in comments:
                e, weight, _ = line.split()
                E.append(float(e))
                ensemble_weights.append(float(weight))
            self.parsed_info["outputs"]["energy_ele"] = np.array(E, dtype=np.float64)
            self.parsed_info["outputs"]["crest_ensemble_weights"] = np.array(
                ensemble_weights, dtype=np.float64
            )
        self.after_parse()
        return self.parsed_info

    def after_parse(self):
        r"""Checks to perform after parsing output file."""
