function initCube(texturePath, faces) {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer();
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);

  const video = document.createElement('video');
  video.src = texturePath;
  video.muted = true;
  video.loop = true;
  video.autoplay = true;
  video.play();

  const videoTexture = new THREE.VideoTexture(video);
  const materials = faces.map(f => {
    const mat = new THREE.MeshBasicMaterial({ map: videoTexture });
    mat.userData = { link: f.link };
    return mat;
  });

  const geometry = new THREE.BoxGeometry();
  const cube = new THREE.Mesh(geometry, materials);
  scene.add(cube);
  camera.position.z = 3;

  function animate() {
    requestAnimationFrame(animate);
    cube.rotation.x += 0.005;
    cube.rotation.y += 0.01;
    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener("click", () => {
    const faceIndex = Math.floor(Math.random() * 6);
    const link = materials[faceIndex].userData.link;
    if (link) window.open(link, "_blank");
  });
}
