"""Find faces in the images and group images by person.

Arguments:
    source: directory with the photos. Script will browse it recursively and find all image files.
    target: directory with the clustering results. For each person there will be a subdirectory
        with the photos of that person, and a metadata.json file with the information about the
        original file and the location of the face in it.
    known_images: optional text file with the list of the images to process. If not provided, all
    images in the source directory will be processed.
"""
import collections
import json
import logging
import mimetypes
import os
import pathlib
import shutil
import sys
from multiprocessing import Pool, cpu_count
from PIL import Image, ImageDraw

import face_recognition
import numpy as np
from sklearn.cluster import DBSCAN

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s  %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
nprocs = cpu_count()

Face = collections.namedtuple("Face", ["enc", "img", "location"])

def is_image(fname: pathlib.Path) -> bool:
    mime, _ = mimetypes.guess_type(fname)
    return mime is not None and mime.startswith("image/")


def extract_faces(img: pathlib.Path) -> list[Face]:
    image = face_recognition.load_image_file(img)
    face_locations = face_recognition.face_locations(image)
    faces = face_recognition.face_encodings(image, face_locations)
    logger.info("found %d faces in %s", len(faces), img)
    return [Face(face, img, location) for face, location in zip(faces, face_locations)]

def mark_face(img: pathlib.Path, pos: list[int]):
    image = Image.open(img)
    draw = ImageDraw.Draw(image)
    draw.rectangle(xy=[(pos[3], pos[0]), (pos[1], pos[2])])
    image.save(img)

def copy_resolve_duplicates(imgs: list[pathlib.Path], target_dir: pathlib.Path) -> dict[pathlib.Path, str]:
    seen = set()
    actual_names = {}
    for img in imgs:
        counter = 0
        actual_name = f"{img.name}"
        while actual_name in seen:
            actual_name = f"{img.stem}_{counter}{img.suffix}"
            counter += 1
        shutil.copy(img, target_dir / actual_name)
        actual_names[img] = actual_name
        seen.add(actual_name)
    return actual_names

def main(source, target, known_images):
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

    all_faces = []
    with Pool(nprocs) as pool:
        for fimg in pool.map(extract_faces, images):
            all_faces.extend(fimg)

    logger.info("found %d faces in %d files", len(all_faces), len(images))
    if not all_faces:
        logger.info("No faces found in any images.")
        return

    logger.info("grouping the files by face")
    enc_faces = np.vstack([f.enc for f in all_faces])

    cluster = DBSCAN(eps=0.5, min_samples=1, metric="euclidean", algorithm="ball_tree", leaf_size=40, n_jobs=-1).fit(enc_faces)

    groups = collections.defaultdict(list)
    for label, face in zip(cluster.labels_, all_faces):
        if label == -1:
            continue
        groups[label].append(face)
    logger.info("found %d groups", len(groups))

    image_to_face = collections.defaultdict(list)
    for label, faces in groups.items():
        person_dir = target / f"person_{label:06d}"
        os.makedirs(person_dir, exist_ok=True)
        actual_names = copy_resolve_duplicates([f.img for f in faces], person_dir)

        metadata = collections.defaultdict(list)
        for face in faces:
            image_to_face[str(face.img)].append(int(label))
            name = actual_names[face.img]
            metadata[name].append({
                "origin": str(face.img),
                "location": list(map(int, face.location))
            })
            mark_face(person_dir / name, face.location)
        (person_dir / "metadata.json").write_bytes(json.dumps(metadata).encode("utf-8"))
    (target / "metadata.json").write_bytes(json.dumps(image_to_face).encode("utf-8"))


if __name__ == "__main__":
    source, target = sys.argv[1], sys.argv[2]
    known_images = None
    if len(sys.argv) == 4:
        known_images = pathlib.Path(sys.argv[3])

    logger.info("Source: %s, target: %s, known images: %s", source, target, known_images)

    main(pathlib.Path(source), pathlib.Path(target), known_images)
