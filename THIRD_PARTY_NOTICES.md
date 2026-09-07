# Third-party library data

The KiCad community provides the standard symbols, footprints and 3D model references used by this project. See the [KiCad library license](https://gitlab.com/kicad/libraries/kicad-footprints/-/blob/master/LICENSE.md): CC BY-SA 4.0 with the KiCad electronic-design exception.

The project-local footprint collection in `hardware/Matrix6/DevBoard.pretty` contains modified KiCad library footprints and is distributed under that same library license. A copy of the upstream notice is included as `DevBoard.pretty/LICENSE.md`.

- `ESP32-S3-WROOM-1_Edge` derives from `RF_Module:ESP32-S3-WROOM-1`. The project changes the antenna/board-edge accommodation; standard module pad positions are retained.
- `USB4105_NoUnderbodyCopper` derives from `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`. The project adds the named F.Cu track/via/pour keepout for the connector body; standard connector pad positions are retained.

Matrix5 interface references are derived from the owner's MatrixFive designs and the public [FaBoAI/Matrix5](https://github.com/FaBoAI/Matrix5) project. The raw private EasyEDA project was not included in this repository.
