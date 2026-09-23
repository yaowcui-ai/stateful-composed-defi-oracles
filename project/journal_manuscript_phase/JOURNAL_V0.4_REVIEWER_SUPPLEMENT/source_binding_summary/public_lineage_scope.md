# G3 pairwise lineage audit v1

## Method and claim boundary

Lineage was assessed from affirmative repository origin statements, controller inheritance/import paths, official GitHub path histories, deployment-era source correspondence, and controller-source copy-overlap screening. Behavioral difference alone was not used. Absence of a discovered fork alone was not used. Shared interfaces and generic Solidity/library fragments were not treated as copying.

`L3` retains the frozen lineage level. Here it is separately qualified as `BOUNDED_PUBLIC_PROVENANCE`: the relevant controllers are independently implemented **within the inspected public repository histories and bound source trees**. It does not assert the absence of private or unpublished ancestry. This scope qualifier must be retained in later claims.

## Results

- Vesta–Felix: **L2**. Vesta affirmatively states it is forked from Liquity; Felix affirmatively identifies Liquity V2 code and Felix modifications. The relevant Felix terminal controller is modified but shares conceptual/project ancestry.
- All other nine pairs among Vesta, Mento, Aurigami, Fathom, and Felix: **L3**, qualified as `BOUNDED_PUBLIC_PROVENANCE`. Each has affirmative, distinct controller origin/path history and inheritance evidence, with only low generic eight-token overlap in the inspected sources.

The CSV matrix and `G3_CONTROLLER_PROVENANCE_EVIDENCE.json` contain pair-level evidence and scope limits. These results permit a carefully qualified cross-implementation comparison; they do not justify an unqualified universal independence claim.
