from pytorch_lightning import Trainer
from monoscene.models.monoscene import MonoScene
from monoscene.data.NYU.nyu_dm import NYUDataModule
from monoscene.data.semantic_kitti.kitti_dm import KittiDataModule
from monoscene.data.nuscenes.nuscenes_dm import NuScenesDataModule
import hydra
from omegaconf import DictConfig
import torch
import os
from hydra.utils import get_original_cwd
import ipdb


@hydra.main(config_name="../config/monoscene-kitti.yaml")
def main(config: DictConfig):
    # ipdb.set_trace()
    torch.set_grad_enabled(False)
    if config.dataset == "kitti":
        config.batch_size = 1
        config.n_gpus = 1
        n_classes = 20
        feature = 64
        project_scale = 2
        full_scene_size = (256, 256, 32)
        data_module = KittiDataModule(
            root=config.kitti_root,
            preprocess_root=config.kitti_preprocess_root,
            frustum_size=config.frustum_size,
            batch_size=int(config.batch_size / config.n_gpus),
            num_workers=int(config.num_workers_per_gpu * config.n_gpus),
        )

    elif config.dataset == "nuscenes":
        full_scene_size = (256, 256, 32)
        project_scale = 2
        feature = 64
        n_classes = 13
        data_module = NuScenesDataModule(
            root=config.nuscenes_root,
            preprocess_root=config.nuscenes_preprocess_root,
            frustum_size=config.frustum_size,
            batch_size=int(config.batch_size / config.n_gpus),
            num_workers=int(config.num_workers_per_gpu),
        )

    elif config.dataset == "NYU":
        config.batch_size = 2
        project_scale = 1
        n_classes = 12
        feature = 200
        full_scene_size = (60, 36, 60)
        data_module = NYUDataModule(
            root=config.NYU_root,
            preprocess_root=config.NYU_preprocess_root,
            n_relations=config.n_relations,
            frustum_size=config.frustum_size,
            batch_size=int(config.batch_size / config.n_gpus),
            num_workers=int(config.num_workers_per_gpu * config.n_gpus),
        )

    trainer = Trainer(
        sync_batchnorm=True, deterministic=True, gpus=config.n_gpus, accelerator="gpu"
    )

    if config.dataset == "NYU":
        model_path = os.path.join(
            get_original_cwd(), "trained_models", "monoscene_nyu.ckpt"
        )
    else:
        model_path = "/data4/sas20048/SSCBench/results/ckpts/kitti/monoscene_kitti.ckpt"

    model = MonoScene.load_from_checkpoint(
        model_path,
        feature=feature,
        project_scale=project_scale,
        fp_loss=config.fp_loss,
        full_scene_size=full_scene_size,
    )
    model.eval()
    data_module.setup()
    test_dataloader = data_module.test_dataloader()
    trainer.test(model, test_dataloaders=test_dataloader)


if __name__ == "__main__":
    main()
