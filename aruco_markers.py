import cv2
import os
import numpy as np
from pathlib import Path


class ArUcoMarkers:
    def __init__(self):
        self.output_markers: Path = Path("aruco_markers")
        self.output_calibration_images: Path = Path("fotos_calibracao")
        self.output_cam_parameters: Path = Path("parametros_camera.npz")

        self.marker_size_mm: int = 170
        self.border_mm: int = 20
        self.dpi: int = 300
        self.mm_per_inch: float = 25.4
        self.marker_ids: list[int] = [0, 1, 2, 3]

        self.board_size: tuple[int, int] = (10, 7)
        self.square_length: float = 0.025
        self.marker_length: float = 0.01875

        self.dictionary: cv2.aruco.Dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.board: cv2.aruco.CharucoBoard = cv2.aruco.CharucoBoard(
            self.board_size,
            self.square_length,
            self.marker_length,
            self.dictionary
        )
        self.detector: cv2.aruco.CharucoDetector = cv2.aruco.CharucoDetector(self.board)

        self._create_directories()

    def _create_directories(self):
        self.output_markers.mkdir(parents=True, exist_ok=True)
        self.output_calibration_images.mkdir(parents=True, exist_ok=True)

    def generate_charuco_board_image(self):
        board_image: np.ndarray = self.board.generateImage((2000, 3000))
        filename: Path = self.output_markers / "charuco_board.png"
        cv2.imwrite(str(filename), board_image)
        print(f"Tabuleiro ChArUco gerado em: {filename}")

    def generate_markers(self):
        marker_pixels: int = round(self.marker_size_mm * self.dpi / self.mm_per_inch)
        border_pixels: int = round(self.border_mm * self.dpi / self.mm_per_inch)

        for marker_id in self.marker_ids:
            marker: np.ndarray = np.zeros((marker_pixels, marker_pixels), dtype=np.uint8)
            cv2.aruco.generateImageMarker(self.dictionary, marker_id, marker_pixels, marker)

            marker = cv2.copyMakeBorder(
                marker, border_pixels, border_pixels, border_pixels, border_pixels,
                cv2.BORDER_CONSTANT, value=255
            )

            filename: Path = self.output_markers / f"aruco_{marker_id}.png"
            cv2.imwrite(str(filename), marker, [
                cv2.IMWRITE_PNG_COMPRESSION, 0,
                cv2.IMWRITE_PNG_STRATEGY, cv2.IMWRITE_PNG_STRATEGY_DEFAULT
            ])
            print(f"Marcador {marker_id} gerado: {filename}")

    def _detect_board(self, gray_image: np.ndarray):
        result = self.detector.detectBoard(gray_image)

        if len(result) == 4:
            charuco_corners, charuco_ids, _, _ = result
        else:
            charuco_corners, charuco_ids = result[:2]

        detected: bool = False
        if (charuco_corners is not None and charuco_ids is not None
                and len(charuco_corners) > 4 and len(charuco_corners) == len(charuco_ids)):
            detected = True

        return detected, charuco_corners, charuco_ids

    def _draw_ui(self, display_frame: np.ndarray, count: int, detected: bool, corners: np.ndarray):
        if detected and corners is not None:
            for corner in corners:
                pt: tuple[int, int] = tuple(corner.ravel().astype(int))
                cv2.circle(display_frame, pt, 5, (0, 255, 0), -1)

        status: str = "CharUco Detectado" if detected else "Aproxime o CharUco"
        color: tuple[int, int, int] = (0, 255, 0) if detected else (0, 0, 255)

        cv2.putText(display_frame, f"Fotos: {count}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.putText(display_frame, status, (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    def capture_board(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Não foi possível abrir a câmera")

        count: int = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            clean_frame: np.ndarray = frame.copy()
            display_frame: np.ndarray = frame.copy()
            gray: np.ndarray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            detected, charuco_corners, _ = self._detect_board(gray)
            self._draw_ui(display_frame, count, detected, charuco_corners)

            cv2.imshow("Captura ChArUco", display_frame)
            key: int = cv2.waitKey(1) & 0xFF

            if key in (ord(" "), ord("s")):
                if detected:
                    filename: str = os.path.join(self.output_calibration_images, f"foto_{count + 1:02d}.png")
                    cv2.imwrite(filename, clean_frame)
                    count += 1
                    print(f"[{count}] Foto salva: {filename}")
                else:
                    print("CharUco não detectado! Foto não salva.")
            elif key in (ord("q"), 27):  # 27 é a tecla ESC
                break

        cap.release()
        cv2.destroyAllWindows()
        print(f"\nCaptura finalizada ({count} imagens salvas).")

    def _get_image_files(self):
        images: list[Path] = sorted(self.output_calibration_images.glob("*.png"))
        if not images:
            raise RuntimeError(f"Nenhuma imagem encontrada em {self.output_calibration_images}")
        return images

    def process_images(self):
        images: list[Path] = self._get_image_files()

        object_points: list = []
        image_points: list = []
        image_size = None

        for image_path in images:
            image: np.ndarray = cv2.imread(str(image_path))

            gray: np.ndarray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if image_size is None:
                image_size = gray.shape[::-1]

            detected, charuco_corners, charuco_ids = self._detect_board(gray)

            if not detected or len(charuco_ids) < 8:
                print(f"[IGNORADA] {image_path.name} - Pontos insuficientes")
                continue

            obj_pts, img_pts = self.board.matchImagePoints(charuco_corners, charuco_ids)

            if len(obj_pts) < 8:
                print(f"[IGNORADA] {image_path.name} - matchImagePoints falhou")
                continue

            object_points.append(obj_pts)
            image_points.append(img_pts)
            print(f"[OK] {image_path.name} ({len(charuco_ids)} cantos validos)")

        return object_points, image_points, image_size

    def calibrate_cam(self):
        """Calcula os parâmetros intrínsecos e de distorção da camera."""
        print("\nCalculando parâmetros da câmera...\n")
        object_points, image_points, image_size = self.process_images()

        if not object_points:
            print("Nenhuma imagem válida para calibração. Abortando.")
            return

        rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            object_points, image_points, image_size, None, None
        )

        np.savez(
            self.output_cam_parameters,
            camera_matrix=camera_matrix,
            dist_coeffs=dist_coeffs,
            image_size=image_size,
            rms=rms,
        )
        print(f"Calibração concluída! Erro RMS: {rms:.4f}")
        print(f"Parâmetros salvos em: {self.output_cam_parameters}")