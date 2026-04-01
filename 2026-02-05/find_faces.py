import logging
import mimetypes
import pathlib
import sys

from multiprocessing import cpu_count


import cv2
from concurrent.futures import ThreadPoolExecutor
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import euclidean_distances
import numpy as np
import hdbscan
import db

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s  %(message)s", level=logging.INFO)
app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
logger = logging.getLogger(__name__)
nprocs = cpu_count() // 2

def is_image(fname: pathlib.Path) -> bool:
    mime, _ = mimetypes.guess_type(fname)
    return mime is not None and mime.startswith("image/")

def compare_faces(all_faces):
    enc_faces = np.vstack([f.enc for f in all_faces])
    dist_matrix = euclidean_distances(enc_faces, enc_faces).astype(np.float64)
    for i in range(len(all_faces)):
        for j in range(i + 1, len(all_faces)):
            if all_faces[i].img == all_faces[j].img:
                dist_matrix[i, j] = 999.0
                dist_matrix[j, i] = 999.0
    return dist_matrix

def extract_faces(image_path: pathlib.Path) -> list[db.Face]:
    img = cv2.imread(image_path)
    if img is None:
        return []
    faces = app.get(img)
    logger.info("found %d faces in %s", len(faces), image_path)
    return [db.Face(face.normed_embedding, image_path, list(map(int, face.bbox)), None) for face in faces]

def main(source, target, known_images):
    dbc = db.DB(target)
    images = []
    if known_images:
        logger.info("loading images from file %s", known_images)
        images = list(map(pathlib.Path, known_images.read_text().strip().split("\n")))
    else:
        logger.info("enumerating images")
        images = list(filter(is_image, source.rglob("*")))

    logger.info("images found: %d", len(images))
    if not images:
        logger.info("no images found, stopping")
        return

    all_faces = dbc.load()

    known_faces = set([f.img for f in all_faces])
    to_check = set(images) - known_faces
    logger.info("known files %d, files to check for faces: %4d", len(known_faces), len(to_check))

    with ThreadPoolExecutor(nprocs) as pool:
        for fimg in pool.map(extract_faces, to_check):
            all_faces.extend(fimg)
    logger.info("found %d faces in %d files", len(all_faces), len(images))
    if not all_faces:
        logger.info("No faces found in any images.")
        return

    if to_check:
        new_faces = [f for f in all_faces if f.img in to_check]
        logger.info("adding missing %d faces to the base", len(new_faces))
        dbc.save(new_faces)

    logger.info("calculating distances between faces")
    dist_matrix = compare_faces(all_faces)

    logger.info("grouping the files by face")
    labels = hdbscan.HDBSCAN(
        cluster_selection_epsilon=0.65,
        cluster_selection_method='eom',
        min_cluster_size=3,
        core_dist_n_jobs=-1,
        min_samples=2,
        metric='precomputed'
    ).fit_predict(dist_matrix)
    del dist_matrix
    logger.info("found %d groups", len(set(labels)))

    labeled = []
    for label, face in zip(labels, all_faces):
        face_list = list(face)
        face_list[-1] = int(label + 1)
        labeled.append(db.Face(*face_list))
    all_faces = labeled

    logger.info("saving %d labeled faces to the database", len(all_faces))
    dbc.save(all_faces)


if __name__ == "__main__":
    source, target = sys.argv[1], sys.argv[2]
    known_images = None
    if len(sys.argv) == 4:
        known_images = pathlib.Path(sys.argv[3])

    logger.info("Source: %s, target: %s, known images: %s", source, target, known_images)

    main(pathlib.Path(source), pathlib.Path(target), known_images)